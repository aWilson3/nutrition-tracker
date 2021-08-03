"""
Informal test cases for nutrition application classes

"""

# Create User object
a = User('Alex')
a.set_weight()
a.set_age()
a.set_sex()
print(a)

# Test User methods
a.add_day()
a.show_daylist()

# Create QueryResult object
results = QueryResult('avocado')
av = results.lookup()
idx = av.find_nutrient('vitamin d')

# Add day object as attribute to User 'Alex'
today = a.get_day(datetime.now().date())
# Add avocado food object as attribute of today
today.add_food(av)

# Add garlic to today
results = QueryResult('garlic')
garlic = results.lookup()
garlic_nutrients = garlic.find_nonzero_nutrients()
today.add_food(garlic)

# Look up a nutrient for garlic
idx = garlic.find_nutrient('calcium')[0]
garlic_calcium = garlic.get_nutrient(idx)

# Get the amount of calcium in garlic as a percentage of
# the daily recommended intake
garlic_calcium.get_dri()
