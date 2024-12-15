
def user_status_generator(users:int):
    while users >=0:
        print("users=", users)
        print()
        yield users
        users -=1
