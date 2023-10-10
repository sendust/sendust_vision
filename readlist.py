
def get_decklink_list(config):
    count = 0
    dl = []
    for each in config:
        dl.append(each["decklink"])
    
    return set(dl)
        

def read_config(file_config):
    index = 0
    config = []
    with open(file_config, "r",  encoding='utf-8') as rectangle_file:   # Read rectangle definition file
        lines = rectangle_file.readlines()
        for each in lines[3:]:
            data = [element.strip() for element in each.strip().split(",")]
            config.append({"index" : index, "x" : data[0], "y" : data[1],
            "width" : data[2], "height" : data[3], "name" : data[4], "decklink" : data[5]})
            index += 1
    return config



list_config = read_config('list_dl.txt')

for each in list_config:
    print(each)

print(get_decklink_list(list_config))    
    

    