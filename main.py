class User:
    def __init__(self, user_id, user_name, email):
        self.user_id = user_id
        self.user_name = user_name
        self.email = email

def get_user_by_id(search_id):
    for user in database_simulation:
        if user.user_id == search_id:
            return user
    return "User is not founed!"

user1 = User(1, "Anton", "Ant@gmail.com")
user2 = User(2, "Robert", "Rob@gmail.com")
user3 = User(3, "Tima", "Tima@gmail.com")
database_simulation = [user1, user2, user3]


        
result = get_user_by_id(3)
print(f"Result: {result.user_name}, Email: {result.email}")