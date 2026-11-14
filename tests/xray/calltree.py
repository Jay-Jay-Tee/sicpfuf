# args: -v 2 --trace fib,count_change
def fib(n):
    return n if n <= 1 else fib(n - 1) + fib(n - 2)

def count_change(amount, kinds):
    return (1 if amount == 0
            else 0 if amount < 0 or kinds == 0
            else count_change(amount, kinds - 1) + count_change(amount - kinds * 5, kinds))

def gcd(a, b):
    return a if b == 0 else gcd(b, a % b)

print(fib(4))
print(count_change(10, 2))
print(trace(gcd, 206, 40))
print(measure(gcd, 1071, 462))
