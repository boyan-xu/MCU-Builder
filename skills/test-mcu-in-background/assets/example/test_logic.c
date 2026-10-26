extern int move_player(int position, int delta);
extern void draw_player(int x);
extern unsigned char oled_framebuffer[1024];

int test_main(void) {
    if (move_player(10, 1) != 11) return 1;
    if (move_player(0, -1) != 0) return 2;
    if (move_player(127, 1) != 127) return 3;
    draw_player(64);
    if (oled_framebuffer[64 + 3 * 128] != 1) return 4;
    return 0;
}
