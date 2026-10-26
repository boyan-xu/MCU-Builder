#include <stdint.h>

/* Pure game logic. Hardware-specific display and input code is not included. */
int move_player(int position, int delta) {
    int next = position + delta;
    if (next < 0) return 0;
    if (next > 127) return 127;
    return next;
}

uint8_t oled_framebuffer[1024];
void draw_player(int x) {
    oled_framebuffer[x + 3 * 128] |= 1;
}
