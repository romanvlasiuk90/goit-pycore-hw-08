from datetime import datetime, timedelta
import re
import pickle
from collections import UserDict

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

# Field: Базовий клас для полів запису
class Field: 
    # Ініціалізація класу
    def __init__(self, value):
        self.value = value
    # Код форматування об"єкта як рядка
    def __str__(self):
        return str(self.value)

# Name: Клас для зберігання імені контакту. Обов'язкове поле.
class Name(Field):
    def __init__(self, value):
        # Виклик конструктора базового класу Field
        super().__init__(value)

# Phone: Клас для зберігання номера телефону. Має валідацію формату (10 цифр).
class Phone(Field):
    def __init__(self, value):
        if len(value) != 10 or not value.isdigit():
            raise ValueError("Номер телефону має складатись з 10 цифр", {value})
        # Виклик конструктора базового класу Field
        super().__init__(value)

# Створенню класу Birthday з можливістю додавання поля для дня народження до контакту
class Birthday(Field):
    def __init__(self, value):
        try:
            # Додайте перевірку коректності даних та перетворіть рядок на об'єкт datetime - просто дату
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

# Record: Клас для зберігання інформації про контакт, включаючи ім'я та список телефонів.
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        # Додаємо новий номер в кінець списку через виклик класу Phone
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        # Ітеруємо список телефонів та перезаписуємо у список ті, що не співпадають із вказаним
        new_phones = []
        for p in self.phones:
            if str(p) != phone:
                new_phones.append(p)
        self.phones = new_phones

    def edit_phone(self, old_phone, new_phone):
        # Пошук записів з відповідним телефоном та заміна на новий
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = new_phone

    def find_phone(self, phone):
        # Перебираємо всі номери контакту і повертаємо чи знаходимо вказаний
        for p in self.phones:
            if str(p) == phone:
                return p
        return f"Немає номера {phone}"

    def add_birthday(self, birthday):
        # Перевірка, що день народження ще не встановлено
        if self.birthday is None:
            self.birthday = Birthday(birthday)
        else:
            raise ValueError("Контакт вже містить день народження")

    def __str__(self):
        # Перевірка чи контакт має ДН
        if self.birthday is not None:
            birthday = self.birthday.value.strftime("%d.%m.%Y")
        else:
            birthday = "No birthday set"
        return f"Name: {self.name.value}, Phones: {[p.value for p in self.phones]}, Birthday: {birthday}"

# AddressBook: Клас для зберігання та управління записами.
class AddressBook(UserDict):
    def add_record(self, record):
        # У словник data для зберігання вмісту класу UserDict записуємо значення по імені контакту
        contact_name = record.name.value
        self.data[contact_name] = record
#       return print(f"[contact_name] == {contact_name}, record == {record}")

    def find(self, name):
        # Повертаємо значення із словника data UserDict за ключем - ім"я
        return self.data.get(name)

    def delete(self, name):
        # Видалення запису із словника по ключу/імені
        if name in self.data:
            del self.data[name]
            return print(f"Видалено запис по ключу/імені {name}")
        else:
            return print(f"Не знайдено ключ/імя на видалення")

    def get_upcoming_birthdays(self):
        # Визначте поточну дату системи за допомогою datetime.today().date().
        today = datetime.today().date()
        # Список для зберігання інформації про привітання
        upcoming = []
        # Пройдіться по record та аналізуйте дати народження кожного користувача (for record in values).
        for record in self.data.values():
            if record.birthday:
                # Визначення дати наступного дня народження
                next_birthday = record.birthday.value.replace(year=today.year)
                if next_birthday < today:
                    next_birthday = next_birthday.replace(year=today.year + 1)
                # Перевірка, чи день народження припадає на вихідний
                while next_birthday.weekday() >= 5: # 5 і 6 - субота і неділя
                    next_birthday += timedelta(days=1) # Переносимо наступний день на понеділок
                # Якщо наступне день народження протягом тижня - додаємо до списку привітань
                if 1 <= (next_birthday - today).days <= 7:
                    upcoming.append(f"{record.name.value}: {next_birthday.strftime('%d.%m.%Y')}")
        return upcoming

def parse_input(user_input):
    # Переводимо символи вводу у нижній регістр та розділяємо рядок за пробілами
    cmd, *args = user_input.lower().split()
    return cmd, args

def input_error(func):
    # Декоратор для обробки помилок функцій
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return str(e)
    return inner

def add_contact(args, book):
    if len(args) < 2:
        return "Please provide a name and at least one phone number."
    else:
        name, phone = args[:2]
        record = book.find(name)
        if not record:
            # створюємо новий об"єкт Record з іменем вводу
            record = Record(name)
            # створюємо новий запис
            book.add_record(record)
            message = "Contact added."
        # додаємо телефон до контакту
        record.add_phone(phone)
        return message

@input_error
def change_contact(args, book):
    if len(args) < 3:
        return "Please provide a name and at least old and new phone numbers."
    else:
        # беремо аргументи з поля вводу та призначаємо їм змінні
        name, old_phone, new_phone = args[:3]
        record = book.find(name)
        if not record:
            return f"No contact found with name {name}."
        # Виконуємо перевірку чи існує старий номер у списку 
        if old_phone not in [p.value for p in record.phones]:
            return f"No phone number {old_phone} found for {name}."
        record.edit_phone(old_phone, new_phone)
        return f"Phone number updated for {name}."

@input_error
def show_phone(args, book):
    if len(args) < 1:
        return "Please provide a name of contact"
    else:
        name = args[0]
        record = book.find(name)
        if not record:
            return f"No contact found with name {name}."
        if record.phones:
            return f"{name}'s phone numbers: {', '.join(p.value for p in record.phones)}"
        else:
            return f"No phone numbers found for {name}."

@input_error
def add_birthday(args, book):
    if len(args) != 2:
        return "Please provide a name and birthday date DD.MM.YYYY"
    else:
        name, birthday = args[:2]
        record = book.find(name)
        if not record:
            return f"No contact found with name {name}."
        # Викликаємо функцію додавання ДН з класу Record
        record.add_birthday(birthday)
        return f"Birthday added for {name}."

@input_error
def show_birthday(args, book):
    if len(args) < 1:
        return "Please provide a name of contact"
    else:
        name = args[0]
        record = book.find(name)
        if not record or not record.birthday:
            return f"No birthday set for {name}."
        return f"{name}'s birthday is on {record.birthday.value.strftime('%d.%m.%Y')}."

@input_error
def birthdays(args, book):
    return "\n".join(book.get_upcoming_birthdays())

@input_error
def show_all_contacts(book):
    if book:
        print(f"Contacts:")
        for name, record in book.items():
            print(f"- {name}:")
            for phone in record.phones:
                print(f"  - {phone}")
            if record.birthday:
                print(f"  - Birthday: {record.birthday}")
    else:
        print(f"Address book is empty.")

def main():
    book = load_data()
    #book = AddressBook()
    print("Welcome to the assistant bot! Введіть HELLO щоб розпочати роботу з Ботом")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)
            break

        elif command == "hello":
            print("How can I help you?\n Add Name Phone \n Change Name Phone \n Phone Name \n All \n Add-birthday NAME DD.MM.YYYY \n Show-birthday NAME \n Birthdays \n Exit - Close \n")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            show_all_contacts(book)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()