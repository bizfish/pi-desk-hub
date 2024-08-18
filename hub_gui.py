import pyray as pr


def toggle(x, y, width, height, checked):
    if pr.is_mouse_button_pressed(0) and pr.check_collision_point_rec(
        pr.get_mouse_position(), pr.Rectangle(x, y, width, height)
    ):
        checked = not checked
    # draw
    pr.draw_rectangle(x, y, width, height, pr.SKYBLUE)
    if checked:
        pr.draw_rectangle(
            x + 2,
            y + 2,
            width - 4,
            height - 4,
            pr.BLUE,
        )
    return checked
