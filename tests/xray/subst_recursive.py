# args: -v 1 --subst
def factorial(n):
    return 1 if n == 1 else n * factorial(n - 1)

def fact_iter(product, counter, max_count):
    return (product
            if counter > max_count
            else fact_iter(counter * product, counter + 1, max_count))

print(factorial(4))
fact_iter(1, 1, 3)
