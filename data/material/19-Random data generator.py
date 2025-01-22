import csv
import random
import datetime

# 定义随机数据生成函数
def random_date(start_year, end_year):
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
    random_days = random.randint(0, (end_date - start_date).days)
    return (start_date + datetime.timedelta(days=random_days)).strftime('%B %d, %Y')

def random_name():
    first_names = [
        "Andrij", "Ihor", "Volodymyr", "Oleh", "Dmytro", "Yuriy", "Oleksandr", "Serhiy", "Roman", "Mykola"
    ]
    last_names = [
        "Bibikov", "Sakalo", "Tkachuk", "Shevchenko", "Kovalenko", "Bondarenko", "Kravchenko", "Lysenko", "Hrytsenko", "Zinchenko"
    ]
    middle_names = [
        "Volodymyrovych", "Vasyl'ovych", "Oleksandrovych", "Petrovych", "Mykhailovych", "Yuriyovych", "Serhiyovych", "Romanovych", "Mykolayovych", "Ivanovych"
    ]
    return f"{random.choice(first_names)} {random.choice(last_names)} {random.choice(middle_names)}"

def random_location():
    locations = [
        "Kropyvnyts'kyj, Kropyvnytska urban community, Kropyvnytskyi District, Kirovohrad Oblast",
        "Horinchovo, Horinchivska rural community, Khust District, Zakarpattia Oblast",
        "Donetsk Oblast",
        "Bilohirka, Velykooleksandrivska settlement community, Beryslav District, Kherson Oblast",
        "Kyiv Oblast",
        "Lviv Oblast",
        "Odesa Oblast",
        "Kharkiv Oblast",
        "Zhytomyr Oblast",
        "Chernivtsi Oblast"
    ]
    return random.choice(locations)

def random_sources():
    sources = [
        "https://example1.com", "https://example2.com", "https://example3.com",
        "https://example4.com", "https://example5.com",
        "https://example6.com", "https://example7.com", "https://example8.com",
        "https://example9.com", "https://example10.com"
    ]
    return ", ".join(random.choices(sources, k=random.randint(3, 8)))

# CSV 列名
columns = [
    "#", "Name", "Date of birth", "Date of death", "Date of burial",
    "From", "Died in the area of", "Rank", "Military Unit", "Sources"
]

# 生成随机数据
num_rows = 5000
rows = []
for i in range(num_rows):
    date_of_birth = random_date(1960, 2000)
    date_of_death = random.randint(0,100) # random_date(2022, 2024)
    date_of_burial = random_date(2022, 2024) if random.randint(0, 1) else "?"
    rows.append([
        i,
        random_name(),
        date_of_birth,
        date_of_death,
        date_of_burial,
        random_location(),
        random_location(),
        random.choice(["Captain", "Senior soldier", "Lieutenant", "Major", "Colonel", "Private", "Sergeant"]),
        random.choice(["Unknown", "Battalion 1", "Battalion 2", "Recon Squad", "Special Forces", "Infantry"]),
        random_sources()
    ])

# 写入CSV文件
with open("random_data.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(columns)
    writer.writerows(rows)

print("CSV 文件生成成功：random_data.csv")
