# args: -v 3 --env
def make_withdraw(balance):
    def withdraw(amount):
        nonlocal balance
        if balance >= amount:
            balance = balance - amount
            show_env("inside withdraw(" + str(amount) + ")")
            return balance
        else:
            return "Insufficient funds"
    return withdraw

w1 = make_withdraw(100)
w2 = make_withdraw(100)
w1(30)

def factorial(n):
    if n == 1:
        show_env("deepest point of factorial(3)")
        return 1
    else:
        result = n * factorial(n - 1)
        return result

factorial(3)

xs = llist(1, 2)
ys = xs
zs = llist(1, 2)
counter = 0
def bump():
    global counter
    counter = counter + 1
bump()
