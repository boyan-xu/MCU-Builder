"""Check the published snapshot without building games or accessing hardware."""
from pathlib import Path
import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'showcases/stm-games-v1'


class ShowcaseTests(unittest.TestCase):
    def test_inventory_and_complete_archive(self):
        manifest = json.loads((CASE / 'export-manifest.json').read_text(encoding='utf-8'))
        for name, record in manifest['files'].items():
            data = (CASE / name).read_bytes()
            self.assertEqual(len(data), record['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), record['sha256'])
        with zipfile.ZipFile(CASE / 'firmware-source.zip') as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertEqual(len(names), len(set(names)))
            entries = archive.read('SOURCE_MANIFEST.sha256').decode().splitlines()
            self.assertEqual(len(entries), manifest['sourceFiles'])
            self.assertEqual(len(names), len(entries) + 1)
            for line in entries:
                digest, name = line.split('  ', 1)
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
                self.assertFalse(name.startswith('/') or '..' in Path(name).parts)
                self.assertNotIn(Path(name).name, ('AGENTS.md', 'PROJECT_STATE.json'))
                self.assertFalse(any(part.lower() in ('work', 'debug', 'release', '.git', '__pycache__') for part in Path(name).parts))
            for project in manifest['projectDirectories']:
                for needed in ('.project', '.cproject', 'Core/Inc/main.h', 'Core/Src/main.c', 'Core/Src/stm32f1xx_hal_msp.c', 'Drivers/CMSIS/LICENSE.txt', 'Drivers/STM32F1xx_HAL_Driver/LICENSE.txt', 'STM32F103C8TX_FLASH.ld'):
                    self.assertIn(project + '/' + needed, names)
                self.assertIn(project + '/Core/Startup/startup_stm32f103c8tx.s', names)
            for project in ('000 OLEDGames', '004 OLEDDino'):
                self.assertIn('Chromium', archive.read(project + '/THIRD_PARTY_NOTICES.txt').decode())

    def test_connections_match_published_firmware(self):
        connections = json.loads((CASE / 'connections.json').read_text())
        self.assertFalse(connections['readyToPowerFromThisDocumentAlone'])
        root = ET.parse(CASE / 'wiring.svg').getroot()
        labels = ''.join(root.itertext())
        with zipfile.ZipFile(CASE / 'firmware-source.zip') as archive:
            base = '000 OLEDGames/'
            header = archive.read(base + 'Core/Inc/main.h').decode()
            init = archive.read(base + 'Core/Src/main.c').decode()
            msp = archive.read(base + 'Core/Src/stm32f1xx_hal_msp.c').decode()
            for button, pin in [('UP', 10), ('DOWN', 11), ('LEFT', 12), ('RIGHT', 13), ('OK', 14)]:
                self.assertRegex(header, rf'#define\s+BTN_{button}_Pin\s+GPIO_PIN_{pin}\b')
                self.assertRegex(header, rf'#define\s+BTN_{button}_GPIO_Port\s+GPIOB\b')
                self.assertIn(f'PB{pin}', labels)
            self.assertIn('GPIO_PULLUP', init)
            self.assertRegex(msp, r'PB6\s+------>\s+I2C1_SCL')
            self.assertRegex(msp, r'PB7\s+------>\s+I2C1_SDA')
            for wire in connections['connections']:
                self.assertIn(wire['id'], labels)

    def test_photos_have_no_private_metadata(self):
        for path in (CASE / 'photos').glob('*.jpg'):
            data = path.read_bytes()
            self.assertEqual(data[:2], b'\xff\xd8')
            pos = 2
            while data[pos + 1] != 0xda:
                marker = data[pos + 1]
                self.assertNotIn(marker, range(0xe1, 0xf0))
                self.assertNotEqual(marker, 0xfe)
                pos += 2 + int.from_bytes(data[pos + 2:pos + 4], 'big')

    def test_model_is_not_gcode_and_links_exist(self):
        with zipfile.ZipFile(CASE / 'OLEDGames.3mf') as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn('3D/3dmodel.model', archive.namelist())
            self.assertFalse(any('gcode' in n.lower() for n in archive.namelist()))
        docs = [ROOT / 'README.md', *list((ROOT / 'docs').glob('README.*.md')), *list(CASE.glob('README*.md'))]
        for path in docs:
            for href in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                if '://' in href or href.startswith('#'):
                    continue
                self.assertTrue((path.parent / href.split('#')[0]).exists(), (path, href))


if __name__ == '__main__':
    unittest.main()
