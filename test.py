def a():
    return False

def b():
    return True

while 1:
    print("w")
    if True:
        if False:
            pass
        else:
            if a():
                print("never")
            if b():
                print("b")
                continue
