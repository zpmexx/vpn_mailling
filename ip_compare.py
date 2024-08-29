fortix_dict = {}
zabix_dict = {}

with open ('ip_fortix.txt', 'r') as file:
    for line in file.readlines():
        host, ip = line.strip().split(',')
        fortix_dict[host] = ip

with open ('ip_list.txt', 'r') as file:
    for line in file.readlines():
        host, ip = line.strip().split(',')
        zabix_dict[host] = ip

# Find keys in dict1 not in dict2
missing_in_zabix = {k: fortix_dict[k] for k in zabix_dict if k not in zabix_dict}

# Find keys in dict2 not in dict1
missing_in_fortix = {k: zabix_dict[k] for k in zabix_dict if k not in fortix_dict}

# Find keys in both dicts but with different values
different_values = {k: (fortix_dict[k], zabix_dict[k]) for k in fortix_dict if k in zabix_dict and fortix_dict[k] != zabix_dict[k]}

# Output differences
print("Keys in fortix_dict but not in zabix_dict:", missing_in_zabix)
print("Keys in zabix_dict but not in fortix_dict:", missing_in_fortix)
print("Keys with different values in both dictionaries:", different_values)

with open ('ip_compare_result.txt', 'w') as file:
    for k,v in different_values.items():
        file.write(f"{k} forti ip {v[0]} zabix ip {v[1]}\n")