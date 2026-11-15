# args: -v 4 --typed
def total(xs: LList[int]) -> int:
    return head(xs) + total(tail(xs))

def describe(n: int) -> str:
    if n > 0:
        return "positive"

f = lambda x: x
print(total(llist(1, 2)) + "!")
