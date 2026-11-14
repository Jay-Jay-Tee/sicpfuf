# args: -v 2
from rune import show, heart, sail, stack, beside, quarter_turn_right, make_cross, rcross, stackn
from curve import make_point, draw_connected_full_view_proportional, unit_circle, x_of, y_of
from sound import make_sound, play, get_duration, sine_sound, consecutively
from repeat import repeat_apply

show(make_cross(rcross))
print(repeat_apply(lambda v: v * 2, 10, 1), stackn(2, heart))
draw_connected_full_view_proportional(60)(unit_circle)
print(x_of(unit_circle(0.5)), round(y_of(unit_circle(0.25)), 6))
print(get_duration(consecutively(llist(sine_sound(440, 0.5), sine_sound(660, 0.25)))))
play(make_sound(lambda t: math_sin(2 * math_pi * 440 * t), 0.01))
show(1)
