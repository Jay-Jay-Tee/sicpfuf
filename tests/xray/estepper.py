# args: -v 3 --estep
x = 10
def make_counter():
    count = 0
    def next():
        nonlocal count
        count = count + x
        return count
    return next

c = make_counter()
print(c())
print(c())

def loop(n, acc):
    return acc if n == 0 else loop(n - 1, acc + n)
loop(2, 0)

square = lambda v: v * v
ys = map(square, llist(1, 2))
