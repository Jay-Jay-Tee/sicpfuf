# args: -v 2 --subst
def hypotenuse(a, b):
    def square(x):
        return x * x
    total = square(a) + square(b)
    if total < 0:
        return error("impossible")
    else:
        return math_sqrt(total)

def make_adder(x):
    return lambda y: x + y

size = 3
side = hypotenuse(size, 4)
add_side = make_adder(side)
add_side(1)
map(make_adder(10), llist(1, 2))
True and (False or size > 2)
