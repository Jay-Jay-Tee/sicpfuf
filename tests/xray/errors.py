# args: -v 2
def total(xs):
    return head(xs) + total(tail(xs))

def average(xs):
    return total(xs) / length(xs)

print("start")
print(average(llist(4, 8)))
