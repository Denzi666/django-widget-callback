class SmartDevice:
    def __init__(self, brand, model):
        self.brand = brand
        self.model = model
    

class SmartPhone(SmartDevice):
    def __init__(self, brand, model, ram):
        super().__init__(brand, model)
        self.ram = ram
    
    def phone(self, number):
        print(f"Звоним на номер {number} с телефона {self.brand}...")

phone1 = SmartPhone("Iphone", 15, "8(GB)")
phone1.phone(78481754332)
