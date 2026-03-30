my_favorite_language = "Python"
years_of_learning = 1
likes_programming = True

print(
    f"My favorite language is {my_favorite_language}. " 
    f"I've been learning programming {years_of_learning} year(-s). ",
    f"Do I like programming? {likes_programming}"
    )

years_to_junior = 2
total_experience = years_to_junior + years_of_learning
print(f"My total experience will be {total_experience} year(-s) when I become a junior developer")


my_roadmap = ["Python", "Git","SQL","Django"]
print(f"I'm currently actively learning {my_roadmap[0]}, but once I've learnt it, I'll mvoe on to the next {my_roadmap[3]}.")

known_technologies_count = len(my_roadmap)
if known_technologies_count >= 4:
    print(f"You're ready to on interview. Let's send a resume.")
else:
    print(f"You need to learn a few more frameworks!")


for skill in my_roadmap:
    print(f"I'll definitely learn {skill}.")

def check_job_readiness(roadmap_list):
    lenght_list = len(roadmap_list)
    if lenght_list >= 4:
        return "You are ready!"
    else: 
        return "Keep learning!"

result_message = check_job_readiness(my_roadmap) 
print(result_message)

class SmartDevice:
    def __init__(self, brand, model):
        self.brend = brand
        self.model = model
        self.is_on = False
    
    def turn_on(self):
        self.is_on = True
        print(f"Brand is {self.brend}, model is {self.model} is turned on!")


car1 = SmartDevice("BMW", "M5")
car2 = SmartDevice("Mercedes Benz", "C90")


car1.turn_on()
car2.turn_on()