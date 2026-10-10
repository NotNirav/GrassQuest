"""Second batch of quest templates: many more everyday situations.
Compact rows: (id, title, cat, needs, effort, minutes, time, kind, proof, params, flags)
flags: "wet" = fine in light rain, "rain" = rain-check (window/doorway) quest.
"""

C = ["red", "yellow", "purple", "white", "orange", "pink", "blue"]
ROWS = [
    # --- gentle / low mobility (doorstep, balcony, window) ---
    ("balcony-sky", "Spend {n} minutes on your balcony or doorstep watching the sky change", "mindful", [], 1, 10, "any", "sky", "Your view of the sky", {"n": [5, 10]}, ""),
    ("window-count", "Count every bird that passes your window in 10 minutes", "birds", [], 1, 10, "day", "bird", "Your window view", None, "rain"),
    ("doorstep-tea", "Drink your tea or coffee outside instead of inside", "food", [], 1, 10, "any", "none", "Your cup, outdoors", None, ""),
    ("plant-water", "Water a plant outside, yours or a thirsty one nearby", "nature", [], 1, 5, "day", "plant", "The plant, freshly watered", None, ""),
    ("gate-chat", "Say hello to a neighbour at the gate or in the lane", "social", [], 1, 10, "any", "none", "Your lane", None, ""),
    ("sun-face", "Close your eyes and feel the sun on your face for one minute", "mindful", [], 1, 3, "day", "none", "Where you stood in the sun", None, ""),
    ("breeze-find", "Find the windiest spot near your home", "mindful", [], 1, 10, "any", "none", "The spot", None, ""),
    ("shoes-on", "Put your shoes on and stand outside for 5 minutes. That's it.", "move", [], 1, 5, "any", "none", "Your shoes, outside", None, ""),

    # --- streets & neighbourhood ---
    ("oldest-building", "Find the oldest-looking building in your neighbourhood", "explore", [], 2, 20, "day", "none", "The building", None, ""),
    ("color-door", "Find a {color} door or gate", "explore", [], 2, 15, "day", "none", "The {color} door", {"color": C}, ""),
    ("cycle-spot", "Spot {n} bicycles on one walk", "explore", [], 1, 15, "day", "none", "One of the bicycles", {"n": [3, 5]}, ""),
    ("hand-painted", "Find a hand-painted sign or shop board", "explore", [], 2, 20, "day", "none", "The painted sign", None, ""),
    ("tiny-shop", "Find the smallest shop in your area", "explore", [], 2, 20, "day", "none", "The tiny shop", None, ""),
    ("water-tank", "Find the highest water tank or tower you can see", "explore", [], 1, 10, "day", "none", "The tower", None, ""),
    ("bus-stop", "Walk to the nearest bus stop and back", "move", [], 2, 20, "any", "none", "The bus stop", None, ""),
    ("pattern-floor", "Find an interesting pattern on the ground: tiles, bricks or cracks", "photo", [], 1, 10, "day", "none", "The pattern", None, ""),
    ("reflection-glass", "Find your reflection in a shop window or car", "photo", [], 1, 10, "any", "none", "The reflection", None, ""),
    ("clock-hunt", "Find a public clock or a sundial", "explore", [], 3, 25, "day", "none", "The clock", None, ""),
    ("bridge", "Cross a bridge, footbridge or flyover on foot", "move", [], 3, 30, "day", "none", "The view from the bridge", None, ""),
    ("corner-shop-fruit", "Buy a fruit from a street vendor and eat it outside", "food", [], 2, 15, "day", "plant", "The fruit", None, ""),
    ("graffiti-word", "Find a word written on a wall that you've never noticed", "explore", [], 2, 20, "day", "none", "The word", None, ""),
    ("lane-end", "Walk to the very end of a lane you've never finished", "explore", [], 2, 20, "day", "none", "The end of the lane", None, ""),
    ("animal-sign", "Find a picture of an animal on a sign, wall or truck", "explore", [], 2, 20, "day", "none", "The animal picture", None, ""),

    # --- nature everywhere ---
    ("leaf-big", "Find a leaf bigger than your hand", "nature", [], 1, 10, "day", "tree", "The leaf next to your hand", None, ""),
    ("leaf-small", "Find the smallest leaf you can", "nature", [], 1, 10, "day", "plant", "The tiny leaf on your fingertip", None, ""),
    ("bark-rub", "Find two trees with completely different bark", "nature", ["trees"], 2, 15, "day", "tree", "Either bark, close up", None, ""),
    ("flower-bee", "Find a bee or butterfly visiting a flower", "nature", [], 3, 20, "day", "insect", "The visitor on the flower", None, ""),
    ("ant-trail", "Find an ant trail and follow it for a minute", "nature", [], 1, 10, "day", "insect", "The ants", None, ""),
    ("spider-web", "Find a spider web", "nature", [], 2, 15, "day", "insect", "The web", None, "wet"),
    ("weed-flower", "Find a 'weed' with a beautiful flower", "nature", [], 1, 10, "day", "plant", "The flower", None, ""),
    ("tree-hole", "Find a hole in a tree that might be someone's home", "nature", ["trees"], 2, 20, "day", "tree", "The hole", None, ""),
    ("roots", "Find tree roots breaking through the ground or pavement", "nature", [], 1, 10, "day", "tree", "The roots", None, ""),
    ("seed-fluff", "Find a seed that travels by wind, wings or fluff", "nature", [], 2, 15, "day", "plant", "The seed", None, ""),
    ("bloom-tree", "Find a tree that is flowering right now", "nature", [], 2, 20, "day", "tree", "The blossoms", None, ""),
    ("green-shades", "Find {n} different shades of green", "nature", [], 2, 15, "day", "plant", "Any of the greens", {"n": [3, 5, 7]}, ""),
    ("smell-leaf", "Find a leaf that smells strong when you rub it", "nature", ["garden"], 2, 15, "day", "plant", "The leaf", None, ""),
    ("snail-trail", "Find a snail or a shiny snail trail", "nature", [], 2, 15, "any", "insect", "The snail or trail", None, "wet"),
    ("bird-nest-material", "Spot a bird carrying something in its beak", "birds", [], 4, 30, "day", "bird", "The bird", None, ""),
    ("bird-bath", "Find birds drinking or bathing", "birds", ["water"], 3, 25, "day", "bird", "The birds at the water", None, ""),
    ("pigeon-count", "Count the pigeons in one spot", "birds", [], 1, 5, "day", "bird", "The pigeons", None, ""),
    ("crow-watch", "Watch a crow for 2 minutes and notice what it's doing", "birds", [], 1, 5, "day", "bird", "The crow", None, ""),
    ("parrot", "Spot a parrot or parakeet", "birds", ["trees"], 4, 30, "day", "bird", "The parrot", None, ""),
    ("squirrel", "Spot a squirrel", "nature", ["trees"], 2, 15, "day", "animal", "The squirrel", None, ""),
    ("butterfly-count", "Count butterflies for 10 minutes in {place}", "nature", ["garden"], 3, 15, "day", "insect", "Any butterfly", None, ""),

    # --- parks, water, fields ---
    ("park-lap", "Do {n} laps of {place}", "move", ["park"], 3, 30, "day", "none", "Any part of the lap", {"n": [1, 2, 3]}, ""),
    ("park-bench-read", "Read a few pages of a book on a bench in {place}", "mindful", ["park"], 2, 25, "day", "none", "The book on the bench", None, ""),
    ("park-sketch", "Sketch one thing you see in {place}, however badly", "photo", ["park"], 2, 20, "day", "none", "Your sketch, outdoors", None, ""),
    ("park-yoga", "Do 5 sun salutations or stretches in {place}", "move", ["park"], 2, 15, "day", "none", "Your mat or spot", None, ""),
    ("grass-lie", "Lie on the grass at {place} for 5 minutes", "mindful", ["field"], 1, 10, "day", "plant", "The sky from the grass", None, ""),
    ("cartwheel", "Try a cartwheel, a handstand or a forward roll on grass", "move", ["field"], 3, 10, "day", "none", "The grass where it happened", None, ""),
    ("kite", "Fly a kite, or watch someone else fly one", "social", ["field"], 3, 30, "day", "none", "The kite", None, ""),
    ("water-ripple", "Make ripples on water and watch them spread", "water", ["water"], 2, 20, "day", "none", "The ripples", None, ""),
    ("water-life", "Find something living in or on the water at {place}", "water", ["water"], 3, 25, "day", "animal", "The living thing", None, ""),
    ("lake-loop", "Walk along the edge of {place}", "water", ["water"], 3, 30, "day", "none", "The water", None, ""),
    ("fountain-sit", "Find a fountain or flowing water and listen for 3 minutes", "water", ["water"], 2, 20, "any", "none", "The water", None, ""),
    ("trail-sounds", "Walk {place} and stop 3 times to listen", "move", ["trail"], 3, 35, "day", "none", "The trail", None, ""),
    ("viewpoint-sunset", "Watch the city lights come on from {place}", "sky", ["viewpoint"], 4, 45, "golden", "sky", "The view", None, ""),
    ("cafe-people", "Sit outside at {place} and write down 3 things you notice", "food", ["cafe"], 2, 30, "day", "none", "Your table, outside", None, ""),
    ("playground-swing", "Swing on a swing at {place}. No one's judging.", "social", ["playground"], 2, 15, "day", "none", "The swing", None, ""),

    # --- sky & weather ---
    ("cloud-speed", "Pick one cloud and watch it until it changes shape", "sky", [], 1, 5, "day", "sky", "The cloud", None, ""),
    ("sky-blue", "Photograph the bluest patch of sky you can find", "sky", [], 1, 5, "day", "sky", "The blue sky", None, ""),
    ("sunset-colors", "Name every colour you can see in today's sunset", "sky", [], 2, 20, "golden", "sky", "The sunset", None, ""),
    ("shadow-shape", "Find a shadow that looks like something else", "photo", [], 1, 10, "day", "none", "The shadow", None, ""),
    ("shadow-noon", "Find your shortest shadow of the day", "sky", [], 1, 5, "day", "none", "Your shadow", None, ""),
    ("rain-smell", "Step outside right after rain and breathe in", "rain", [], 1, 5, "any", "none", "The wet ground", None, "rain"),
    ("rain-puddle-sky", "Find the sky reflected in a rain puddle", "rain", [], 1, 10, "any", "sky", "The reflection", None, "rain"),
    ("rain-umbrella", "Take a short walk with an umbrella and listen to it", "rain", [], 2, 10, "any", "none", "The view from under the umbrella", None, "rain"),
    ("rain-flow", "Watch where the rainwater flows from your doorway", "rain", [], 1, 5, "any", "none", "The flowing water", None, "rain"),
    ("rain-leaf", "Find a leaf holding a raindrop", "rain", [], 1, 5, "day", "plant", "The drop on the leaf", None, "rain"),
    ("rain-sound-count", "Count different rain sounds: roof, leaves, road, puddles", "rain", [], 1, 5, "any", "none", "Your window", None, "rain"),
    ("wind-leaves", "Watch leaves dancing in the wind for 2 minutes", "mindful", ["trees"], 1, 5, "day", "tree", "The moving leaves", None, ""),
    ("cool-shade", "Find the coolest patch of shade near you", "mindful", ["trees"], 1, 10, "day", "tree", "The shade", None, ""),
    ("heat-water", "Walk to a tap or water point and splash your face", "mindful", [], 1, 10, "day", "none", "The water", None, ""),
    ("winter-breath", "See your breath in the cold air", "sky", [], 1, 5, "morning", "none", "The cold morning", None, ""),
    ("frost", "Find frost or ice somewhere outside", "nature", [], 3, 15, "morning", "none", "The frost", None, ""),

    # --- movement & fitness ---
    ("walk-minutes", "Walk for {n} minutes in one direction, then come back", "move", [], 2, 30, "any", "none", "The turning point", {"n": [10, 15, 20, 30]}, ""),
    ("brisk", "Walk briskly enough to feel warm for 10 minutes", "move", [], 2, 15, "any", "none", "The road ahead", None, ""),
    ("steps-up", "Find a hill or slope and walk up it", "move", [], 3, 20, "day", "none", "The top", None, ""),
    ("skip-rope", "Skip, jump or hop {n} times outside", "move", [], 2, 10, "any", "none", "Where you jumped", {"n": [30, 50, 100]}, ""),
    ("barefoot-walk", "Walk barefoot on grass or sand for 3 minutes", "move", ["field"], 1, 10, "day", "plant", "Your feet", None, ""),
    ("backwards", "Walk 50 steps backwards (carefully)", "move", ["park"], 2, 10, "day", "none", "Where you ended", None, ""),
    ("run-intervals", "Run fast for 30 seconds, walk for 1 minute, {n} times", "move", [], 4, 20, "any", "none", "Your route", {"n": [5, 8]}, ""),
    ("cycle-new", "Cycle to a place you've never cycled to", "move", [], 4, 40, "day", "none", "Where you arrived", None, ""),
    ("stairs-public", "Take the stairs at a public building or station", "move", [], 2, 10, "day", "none", "The stairs", None, ""),
    ("evening-walk", "Go for an evening walk after dinner", "move", [], 2, 20, "night", "none", "Your street", None, ""),

    # --- kindness & citizen science ---
    ("litter-pick", "Pick up {n} pieces of litter on a walk", "social", [], 2, 20, "day", "none", "The litter before it goes in the bin", {"n": [5, 10, 20]}, ""),
    ("bird-water-bowl", "Leave a bowl of water outside for birds", "birds", [], 1, 10, "day", "bird", "The water bowl", None, ""),
    ("feed-tip", "Find out what the local stray dog or cat is called", "social", [], 2, 20, "day", "animal", "The animal (from a distance)", None, ""),
    ("help-carry", "Help someone carry something, or hold a door, while out", "social", [], 2, 20, "any", "none", "The place it happened", None, ""),
    ("tree-adopt", "Pick a tree near home to 'adopt' and photograph it today", "nature", [], 1, 10, "day", "tree", "Your tree", None, ""),
    ("species-3", "Find {n} different living things in 10 minutes", "nature", [], 2, 15, "day", "plant", "Any of them", {"n": [3, 5, 10]}, ""),
    ("bird-id", "Find a bird you can't name, and let the judge name it", "birds", [], 3, 20, "day", "bird", "The bird", None, ""),
    ("plant-id", "Find a plant you can't name, and let the judge name it", "nature", [], 2, 15, "day", "plant", "The plant", None, ""),
    ("insect-id", "Find a bug you can't name, and let the judge name it", "nature", [], 3, 20, "day", "insect", "The bug", None, ""),

    # --- social & family ---
    ("kids-hunt", "Do a 5-colour scavenger hunt with a kid", "social", [], 2, 20, "day", "none", "Any of the colours", None, ""),
    ("parent-walk", "Take a parent or grandparent for a short walk", "social", [], 2, 20, "any", "none", "The path you walked", None, ""),
    ("pet-new-route", "Walk your pet on a route it's never been on", "social", [], 2, 25, "any", "animal", "Your pet on the new route", None, ""),
    ("friend-race", "Race a friend to a landmark (walking counts)", "social", [], 3, 20, "day", "none", "The landmark", None, ""),
    ("call-walk", "Call a friend, but walk outside the whole time", "social", [], 2, 20, "any", "none", "Where you walked", None, ""),
    ("group-photo-feet", "Take a 'feet in a circle' photo with friends outside", "social", [], 3, 15, "day", "none", "Everyone's feet", None, ""),
    ("cricket-game", "Play a quick game of cricket, football or catch", "social", ["field"], 3, 30, "day", "none", "The game", None, ""),

    # --- campus / office break ---
    ("break-walk", "Take your next break outside instead of at a screen", "mindful", [], 1, 10, "day", "none", "Where you took it", None, ""),
    ("lunch-out", "Eat lunch outside today", "food", [], 2, 30, "day", "none", "Your lunch, outdoors", None, ""),
    ("meeting-walk", "Turn a call or meeting into a walk", "move", [], 2, 30, "day", "none", "Your route", None, ""),
    ("campus-tree", "Find the biggest tree on your campus or office grounds", "nature", [], 2, 15, "day", "tree", "The tree", None, ""),
    ("roof-break", "Go to the highest floor or roof you can and look out", "sky", [], 2, 10, "day", "sky", "The view", None, ""),

    # --- mindful & creative ---
    ("five-senses", "Notice one thing for each of your 5 senses, outside", "mindful", [], 1, 10, "any", "none", "Where you stood", None, ""),
    ("slow-walk", "Walk 100 steps as slowly as you possibly can", "mindful", [], 1, 10, "any", "none", "Your path", None, ""),
    ("gratitude", "Find 3 things outside you're glad exist", "mindful", [], 1, 10, "day", "none", "One of them", None, ""),
    ("sound-map", "Sit for 5 minutes and point to every sound you hear", "mindful", ["bench"], 1, 10, "any", "none", "Your seat", None, ""),
    ("haiku", "Write a 3-line poem about something you see outside", "photo", [], 2, 15, "day", "none", "What inspired it", None, ""),
    ("one-colour-walk", "Walk and only notice {color} things for 5 minutes", "photo", [], 1, 10, "day", "none", "Your favourite {color} thing", {"color": C}, ""),
    ("abstract", "Take an abstract photo: so close no one can tell what it is", "photo", [], 1, 10, "day", "none", "The mystery photo", None, ""),
    ("frame-sky", "Frame the sky between buildings or branches", "photo", [], 1, 10, "day", "sky", "The framed sky", None, ""),
    ("leading-lines", "Find a road, path or fence that leads your eye into the distance", "photo", [], 2, 15, "day", "none", "The leading line", None, ""),
    ("golden-portrait", "Take a photo of a friend in golden-hour light", "photo", [], 2, 15, "golden", "none", "The golden light", None, ""),
    ("night-photo", "Take your best night photo of your street", "photo", [], 2, 15, "night", "none", "The photo", None, ""),

    # --- food & local ---
    ("local-snack", "Try a local snack you've never had, eaten outdoors", "food", [], 2, 20, "day", "none", "The snack", None, ""),
    ("market-fruit", "Find the most colourful fruit stall", "food", [], 2, 20, "day", "plant", "The fruit stall", None, ""),
    ("picnic-mini", "Have a 10-minute mini picnic, even on your doorstep", "food", [], 1, 15, "day", "none", "Your mini picnic", None, ""),
    ("sweet-shop", "Walk to a sweet shop instead of ordering delivery", "food", [], 2, 25, "any", "none", "The shop", None, ""),

    # --- night extras ---
    ("night-moon-shadow", "Find your moon shadow", "sky", [], 3, 15, "night", "sky", "Your shadow by moonlight", None, ""),
    ("night-quiet", "Find the quietest spot within a 5-minute walk", "mindful", [], 2, 15, "night", "none", "The quiet spot", None, ""),
    ("night-planet", "Find the brightest 'star' (it might be a planet)", "sky", [], 2, 10, "night", "sky", "The bright dot", None, ""),
    ("night-flowers", "Find a flower that smells strongest at night", "nature", ["garden"], 3, 20, "night", "plant", "The flower", None, ""),
    ("night-bats", "Watch for bats around street lights or trees", "nature", ["trees"], 3, 20, "night", "animal", "The sky where they flew", None, ""),
]


def templates():
    out = []
    for row in ROWS:
        id_, t, cat, needs, effort, minutes, time_, kind, proof, params, flags = row
        d = dict(id=id_, t=t, cat=cat, needs=needs, effort=effort, min=minutes, time=time_, kind=kind, proof=proof,
                 wet="wet" in flags or "rain" in flags, rain="rain" in flags)
        if params:
            d["params"] = params
        out.append(d)
    return out
