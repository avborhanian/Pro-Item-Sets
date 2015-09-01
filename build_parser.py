import json

'''
    Get only events from timeline that are item related
'''
def get_item_events(frames, participant_id):
    events = []
    for frame in frames:
        if "events" in frame:
            for event in frame["events"]:
                type = event["type"]
                if "ITEM" in type:
                    if event['participantId'] == participant_id:
                        events.append(event)
    return events
    
'''
    Gets the first bought items in the game that were
    bought within 120 seconds of game start
'''
def get_starting_step(events):
    startingThreshold = 120000
    starting_items = []
    if len(events) is 0:
        return None
    while len(events):
        if events[0]["timestamp"] < startingThreshold : 
            starting_items.append(events.pop(0))
        else:
            return process_items(starting_items)
    return process_items(starting_items)
   
''' 
    Gets all items bought before a certain threshold
'''
def get_step(events, max_threshold):
    items = []
    timestamp = 0
    if len(events):
        items.append(events.pop(0))
        timestamp = items[0]['timestamp']
    else:
        return None
    while len(events):
        if max_threshold == -1 or events[0]['timestamp'] < max_threshold:
            items.append(events.pop(0))
            timestamp = items[len(items) - 1]['timestamp']
        else:
            return process_items(items)
    return process_items(items)

'''
    Gets the item builds at various points in the game, and then 
    combines them into an item_set.json type dictionary.
'''
def get_build_steps(frames):
    events = {}
    times = [600000, 1200000, -1]
    types = ["First Purchase", "Early Game", "Mid Game", "End Game", "Final Build"]
    for participant_id in range(1, 11):
        index = 0
        e = get_item_events(frames, participant_id)
        c = list(e)
        item_set = {}
        item_set['type'] = "custom"
        item_set['map'] = "any"
        item_set['mode'] = "any"
        item_set['blocks'] = []
        build = []
        step = get_starting_step(e)
        if step is None:
            events[participant_id] = build
        else:
            block = make_block(types[0], step)
            build.append(block)
        while index < 3:
            step = get_step(e, times[index])
            if step is None or len(step) is 0:
                break
            else:
                block = make_block(types[index + 1], step)
                build.append(block)
            index += 1
        final = process_items(c)
        build.append(make_block(types[4], final))
        item_set['blocks'] = build
        events[participant_id] = item_set

    return events
'''
    Just makes the default block for an item set
'''
def make_block(type, items):
    block = {}
    block['type'] = type
    block['items'] = items
    return block

'''
    So with these item events, some are super useless
    like someone buys an item then undoes that purchase
    So this process_items just acts out what was done 
    in game with the item purchases and what not, and
    spits out the final inventory
'''    
def process_items(item_list):
    timestamp = None
    items = []
    
    for item in item_list:
        item_type = item['type']
        item_name = ""
        if item_type == "ITEM_SOLD" or item_type == "ITEM_PURCHASED":
            item_name = item['itemId']
        amount_to_change = 1
        
        if item_type == "ITEM_UNDO":
            if item['beforeId'] > 0:
                for i in items:
                    if str(i['id']) == str(item['beforeId']):
                        if i['count'] == 1:
                            items.remove(i)
                        else:
                            i['count'] -= 1
                        break;
            else:
                found = False
                for i in items:
                    if str(i['id']) == str(item['afterId']):
                        i['count'] += 1
                        found = True
                        break
                if found is False:
                    items.append({'id': str(item['afterId']), 'count': 1})
            list = "buy" if item['beforeId'] > 0 else "sell"
            amount_to_change = -1
        elif item_type == "ITEM_SOLD":
            for i in items:
                if str(i['id']) == str(item['itemId']):
                    if i['count'] > 1:
                        i['count'] -= 1
                    else:
                        items.remove(i)
                    break
        elif item_type == "ITEM_PURCHASED":
            found = False
            for i in items:
                if str(i['id']) == str(item['itemId']):
                    found = True
                    i['count'] += 1
                    break
            if found == False:
                items.append({'id': str(item['itemId']), 'count': 1})
        else:
            for i in items:
                    if str(i['id']) == str(item['itemId']):
                        if i['count'] > 1:
                            i['count'] -= 1
                        else:
                            items.remove(i)
                        break
    return items
        
# If we just run this class, test the code and make sure it works with our timeline file
if __name__ == "__main__":
    t = open('timeline', 'r')
    j = json.loads(t.read())
    f = j['frames']
    e = get_build_steps(f)
    print json.dumps(e)