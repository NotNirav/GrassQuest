"""Hand-written quest templates. build_quests.py expands params into thousands of concrete quests.

Fields
  t       title; {param} gets filled from params, {place} is filled at runtime with a real nearby place name
  cat     nature | birds | sky | move | explore | water | mindful | photo | social | food | rain
  needs   features that must exist near the player: park, water, trees, viewpoint, bench, trail, garden,
          playground, cafe, field   (street and sky are always available)
  effort  1 (2 minutes on the doorstep) .. 5 (a real expedition)
  min     rough minutes it takes
  time    any | day | golden | night | morning
  wet     True if it's fine (or better) in light rain
  rain    True for rain-check quests: doable from a window/balcony/doorway in bad weather
  kind    what Gemma might identify for the Field Guide: bird | plant | tree | insect | fungus | sky | none
  proof   what a light, honest photo looks like
  params  values to expand
"""

COLORS = ["red", "yellow", "purple", "white", "orange", "pink", "blue"]
SHAPES = ["heart", "star", "circle", "triangle", "letter of your name"]
TEXTURES = ["rough", "smooth", "fuzzy", "spiky", "bumpy"]

T = [
    # ---------- nature ----------
    dict(id="leaf-shapes", t="Find {n} leaves with different shapes", cat="nature", needs=["trees"], effort=1, min=10, time="day", kind="tree", proof="The leaves together in one shot", params={"n": [3, 4, 5]}),
    dict(id="color-grows", t="Find something {color} that grows", cat="nature", needs=[], effort=1, min=10, time="day", kind="plant", proof="The {color} plant, flower or fruit, still growing", params={"color": COLORS}),
    dict(id="touch-grass", t="Touch actual grass. Yes, really.", cat="nature", needs=["field"], effort=1, min=5, time="any", kind="plant", proof="Your hand on real grass"),
    dict(id="tree-hug", t="Find a tree wider than your arms can reach", cat="nature", needs=["trees"], effort=2, min=15, time="day", kind="tree", proof="The trunk, ideally with your arms for scale"),
    dict(id="tiny-flower", t="Find a flower smaller than your fingernail", cat="nature", needs=[], effort=2, min=15, time="day", kind="plant", proof="The tiny flower next to a fingertip"),
    dict(id="moss", t="Find moss growing somewhere unexpected", cat="nature", needs=[], effort=2, min=15, time="day", wet=True, kind="plant", proof="Moss on a wall, step, rock or tree"),
    dict(id="seed", t="Find a seed, pod or pinecone", cat="nature", needs=["trees"], effort=2, min=15, time="day", kind="tree", proof="The seed or pod in your hand"),
    dict(id="crack-plant", t="Find a plant growing out of a crack in concrete", cat="nature", needs=[], effort=1, min=10, time="day", kind="plant", proof="The plant and the crack it beat"),
    dict(id="texture-hunt", t="Find the most {tex} thing in nature you can", cat="nature", needs=[], effort=1, min=10, time="day", kind="plant", proof="A close-up of the {tex} thing", params={"tex": TEXTURES}),
    dict(id="three-trees", t="Find {n} different kinds of tree in {place}", cat="nature", needs=["park"], effort=3, min=30, time="day", kind="tree", proof="Any one of them; the Ranger trusts you on the rest", params={"n": [3, 4, 5]}),
    dict(id="fallen-leaf", t="Find the most colourful fallen leaf on the ground", cat="nature", needs=["trees"], effort=1, min=10, time="day", kind="tree", proof="The leaf on your palm"),
    dict(id="mushroom", t="Find a mushroom or fungus (look, don't eat)", cat="nature", needs=["trees"], effort=3, min=25, time="day", wet=True, kind="fungus", proof="The fungus where it grows"),
    dict(id="bug", t="Spot an insect, snail or spider going about its day", cat="nature", needs=[], effort=2, min=15, time="day", wet=True, kind="insect", proof="The little creature, any distance"),
    dict(id="butterfly", t="Photograph a butterfly or moth", cat="nature", needs=["garden"], effort=4, min=30, time="day", kind="insect", proof="The butterfly or moth"),
    dict(id="four-leaf", t="Hunt for a four-leaf clover in {place}", cat="nature", needs=["field"], effort=5, min=40, time="day", kind="plant", proof="The clover, leaves clearly visible"),
    dict(id="shape-nature", t="Find a {shape} shape hiding in nature", cat="nature", needs=[], effort=2, min=15, time="day", kind="none", proof="The natural {shape}", params={"shape": SHAPES}),
    dict(id="flower-count", t="Find {n} flowers of different colours", cat="nature", needs=["garden"], effort=2, min=20, time="day", kind="plant", proof="Any of them, or all in one frame", params={"n": [3, 4, 5]}),
    dict(id="oldest-tree", t="Find the oldest-looking tree in {place}", cat="nature", needs=["park"], effort=3, min=30, time="day", kind="tree", proof="The old tree"),

    # ---------- birds ----------
    dict(id="bird", t="Spot a bird and photograph it", cat="birds", needs=[], effort=2, min=15, time="day", kind="bird", proof="A real bird, any distance"),
    dict(id="bird-two", t="Photograph two different kinds of bird", cat="birds", needs=["trees"], effort=3, min=30, time="morning", kind="bird", proof="Either bird; both is a flex"),
    dict(id="feather", t="Find a feather on the ground", cat="birds", needs=["park"], effort=3, min=25, time="day", kind="bird", proof="The feather"),
    dict(id="bird-flight", t="Catch a bird mid-flight", cat="birds", needs=[], effort=4, min=30, time="day", kind="bird", proof="A bird with its wings open"),
    dict(id="bird-water", t="Find a bird near water at {place}", cat="birds", needs=["water"], effort=4, min=40, time="day", kind="bird", proof="A bird and water in the same shot"),
    dict(id="nest", t="Spot a bird's nest", cat="birds", needs=["trees"], effort=5, min=40, time="day", kind="bird", proof="The nest, from a respectful distance"),
    dict(id="bird-song", t="Stand still for {n} minutes and count every bird call you hear", cat="birds", needs=["trees"], effort=2, min=10, time="morning", kind="bird", proof="Where you stood (the sky or trees above you)", params={"n": [3, 5]}),
    dict(id="bird-sky", t="Count the birds crossing the sky in {n} minutes", cat="birds", needs=[], effort=1, min=8, time="day", kind="bird", proof="The patch of sky you watched", params={"n": [3, 5]}),

    # ---------- sky ----------
    dict(id="sunset-high", t="Watch the sunset from somewhere high", cat="sky", needs=[], effort=3, min=30, time="golden", kind="sky", proof="The sunset sky"),
    dict(id="sunset-view", t="Catch the sunset from {place}", cat="sky", needs=["viewpoint"], effort=4, min=45, time="golden", kind="sky", proof="The sunset from the viewpoint"),
    dict(id="golden-tree", t="Find golden-hour light hitting a tree", cat="sky", needs=["trees"], effort=2, min=20, time="golden", kind="tree", proof="Warm low light on leaves or bark"),
    dict(id="cloud-animal", t="Find a cloud shaped like a {thing}", cat="sky", needs=[], effort=1, min=5, time="day", kind="sky", proof="The cloud; imagination counts", params={"thing": ["dog", "dragon", "fish", "bird", "face", "shoe"]}),
    dict(id="look-up", t="Lie down and photograph straight up", cat="sky", needs=["field"], effort=1, min=10, time="day", kind="sky", proof="Straight up: sky, branches, clouds"),
    dict(id="moon-day", t="Find the moon in daylight", cat="sky", needs=[], effort=3, min=10, time="day", kind="sky", proof="The moon in a bright sky"),
    dict(id="long-shadow", t="Photograph your shadow when it's taller than you", cat="sky", needs=[], effort=1, min=10, time="golden", kind="none", proof="Your long shadow on the ground"),
    dict(id="star", t="Find {n} stars in the night sky", cat="sky", needs=["field"], effort=3, min=20, time="night", kind="sky", proof="The night sky (stars are hard to photograph; the sky is enough)", params={"n": [2, 3, 5]}),
    dict(id="sky-colors", t="Photograph the sky at its most colourful moment today", cat="sky", needs=[], effort=2, min=15, time="golden", kind="sky", proof="A colourful sky"),
    dict(id="cloud-types", t="Find {n} different types of cloud", cat="sky", needs=[], effort=2, min=15, time="day", kind="sky", proof="Any of the clouds", params={"n": [2, 3]}),

    # ---------- movement ----------
    dict(id="walk-km", t="Walk {km} km without looking at your phone", cat="move", needs=[], effort=3, min=30, time="any", proof="Anything you saw on the way", params={"km": [1, 2, 3]}),
    dict(id="walk-to-place", t="Walk to {place} and back", cat="move", needs=["park"], effort=3, min=35, time="day", proof="A photo at {place}"),
    dict(id="run", t="Go for a {min_run}-minute run or jog", cat="move", needs=[], effort=4, min=25, time="any", proof="Your shoes, the path, or your sweaty victory face", params={"min_run": [10, 15, 20, 30]}),
    dict(id="stairs", t="Find outdoor stairs and climb them {n} times", cat="move", needs=[], effort=3, min=15, time="day", proof="The stairs from the top", params={"n": [2, 3, 5]}),
    dict(id="new-street", t="Walk down a street you've never walked before", cat="move", needs=[], effort=2, min=20, time="day", proof="The new street"),
    dict(id="trail", t="Walk a trail or footpath at {place}", cat="move", needs=["trail"], effort=4, min=45, time="day", proof="The trail ahead of you"),
    dict(id="steps-loop", t="Do a loop around {place}", cat="move", needs=["park"], effort=2, min=20, time="day", proof="Any spot on the loop"),
    dict(id="sunrise-walk", t="Go for a walk before 8 AM", cat="move", needs=[], effort=3, min=20, time="morning", proof="Morning light outside"),
    dict(id="highest-point", t="Reach the highest point you can walk to", cat="move", needs=[], effort=5, min=60, time="day", proof="The view from the top"),
    dict(id="far-walk", t="Walk until you can't see your home", cat="move", needs=[], effort=3, min=25, time="day", proof="Where you ended up"),
    dict(id="cycle", t="Ride a bike for {min_run} minutes", cat="move", needs=[], effort=4, min=30, time="day", proof="The bike outside, or the road ahead", params={"min_run": [15, 30]}),
    dict(id="stretch-outside", t="Do {n} minutes of stretching outside", cat="move", needs=["field"], effort=1, min=10, time="any", proof="Your spot (mat, grass, bench)", params={"n": [5, 10]}),

    # ---------- explore ----------
    dict(id="old-door", t="Find the oldest-looking door in your area", cat="explore", needs=[], effort=2, min=20, time="day", proof="The weathered door"),
    dict(id="street-art", t="Find a piece of street art or a mural", cat="explore", needs=[], effort=3, min=25, time="day", proof="The art"),
    dict(id="color-walk", t="Find {n} {color} things on one street", cat="explore", needs=[], effort=2, min=15, time="day", proof="Any of them", params={"n": [3, 5], "color": COLORS}),
    dict(id="bench-sit", t="Sit on a bench outside for 5 minutes and just watch", cat="explore", needs=["bench"], effort=1, min=10, time="any", proof="The view from the bench"),
    dict(id="playground", t="Visit {place}. Swinging is allowed.", cat="explore", needs=["playground"], effort=2, min=20, time="day", proof="The playground"),
    dict(id="hidden-path", t="Find a shortcut or path you've never taken", cat="explore", needs=[], effort=2, min=20, time="day", proof="The path"),
    dict(id="number-hunt", t="Find the number {num} somewhere outside", cat="explore", needs=[], effort=2, min=15, time="day", proof="The number in the wild", params={"num": [7, 13, 21, 42, 99]}),
    dict(id="letter-hunt", t="Spell your initials using letters you find outdoors", cat="explore", needs=[], effort=3, min=25, time="day", proof="One of the letters"),
    dict(id="map-corner", t="Walk to the edge of {place} you've never been to", cat="explore", needs=["park"], effort=3, min=30, time="day", proof="That far corner"),
    dict(id="viewpoint", t="Get to {place} and take in the view", cat="explore", needs=["viewpoint"], effort=4, min=40, time="day", proof="The view"),
    dict(id="fountain", t="Find a drinking fountain or public tap", cat="explore", needs=[], effort=2, min=15, time="day", proof="The fountain"),

    # ---------- water ----------
    dict(id="reflection", t="Find the sky reflected in water", cat="water", needs=["water"], effort=2, min=20, time="day", wet=True, kind="sky", proof="A reflection in a puddle, pond or lake"),
    dict(id="moving-water", t="Find moving water at {place}", cat="water", needs=["water"], effort=3, min=30, time="day", proof="Flowing water"),
    dict(id="puddle", t="Find a puddle. Jumping is optional.", cat="water", needs=[], effort=1, min=10, time="any", wet=True, proof="The puddle"),
    dict(id="water-sit", t="Sit by the water at {place} for {n} minutes", cat="water", needs=["water"], effort=3, min=25, time="day", proof="The water from where you sat", params={"n": [5, 10]}),
    dict(id="skip-stone", t="Skip a stone on water at {place}", cat="water", needs=["water"], effort=4, min=30, time="day", proof="The water, or the stone in your hand"),
    dict(id="waterfall", t="Find water falling over an edge (fountains count)", cat="water", needs=["water"], effort=5, min=45, time="day", proof="The falling water"),

    # ---------- mindful ----------
    dict(id="sounds", t="Close your eyes outside and count {n} different sounds", cat="mindful", needs=[], effort=1, min=5, time="any", proof="Where you sat or stood", params={"n": [3, 5, 7]}),
    dict(id="sit-still", t="Sit outside for {n} minutes doing absolutely nothing", cat="mindful", needs=["bench"], effort=1, min=10, time="any", proof="Your view", params={"n": [5, 10, 15]}),
    dict(id="barefoot", t="Stand barefoot on grass for 2 minutes", cat="mindful", needs=["field"], effort=1, min=5, time="day", proof="Your feet on grass"),
    dict(id="breathe-tree", t="Take 10 slow breaths under a tree", cat="mindful", needs=["trees"], effort=1, min=5, time="day", kind="tree", proof="The tree from below"),
    dict(id="wind", t="Find something moving in the wind", cat="mindful", needs=[], effort=1, min=5, time="day", proof="Leaves, a flag, clothes, grass"),
    dict(id="smell", t="Find something outside that smells good", cat="mindful", needs=["garden"], effort=1, min=10, time="day", kind="plant", proof="The good-smelling thing"),

    # ---------- photo ----------
    dict(id="frame", t="Frame something beautiful through a gap (branches, a fence, your fingers)", cat="photo", needs=[], effort=2, min=15, time="day", proof="The framed shot"),
    dict(id="macro", t="Take the closest photo you can of something natural", cat="photo", needs=[], effort=1, min=10, time="day", kind="plant", proof="The extreme close-up"),
    dict(id="symmetry", t="Find perfect symmetry outdoors", cat="photo", needs=[], effort=2, min=15, time="day", proof="The symmetrical thing"),
    dict(id="color-palette", t="Photograph a scene that's mostly {color}", cat="photo", needs=[], effort=2, min=15, time="day", proof="The {color} scene", params={"color": COLORS + ["green", "brown", "grey"]}),
    dict(id="light-shadow", t="Find a cool pattern of light and shadow", cat="photo", needs=[], effort=1, min=10, time="day", proof="The pattern"),
    dict(id="tiny-world", t="Photograph a tiny world at ground level", cat="photo", needs=["field"], effort=2, min=10, time="day", kind="plant", proof="Ground-level shot"),

    # ---------- social ----------
    dict(id="friend-walk", t="Go on a walk with a friend", cat="social", needs=[], effort=3, min=30, time="any", proof="Your feet or shadows together (faces optional)"),
    dict(id="dog-spot", t="Spot a dog out on a walk", cat="social", needs=["park"], effort=1, min=15, time="day", proof="The dog (ask before photographing people)"),
    dict(id="park-game", t="Play any game at {place}", cat="social", needs=["park"], effort=3, min=30, time="day", proof="The ball, frisbee, kite or game"),
    dict(id="family-outside", t="Get someone at home to step outside with you for {n} minutes", cat="social", needs=[], effort=2, min=10, time="any", proof="The two of you outside (feet are fine)", params={"n": [5, 10]}),
    dict(id="compliment", t="Say good morning to {n} people on a walk", cat="social", needs=[], effort=2, min=20, time="morning", proof="The street you walked", params={"n": [1, 3]}),

    # ---------- food ----------
    dict(id="snack-out", t="Eat a snack outside, no screens", cat="food", needs=[], effort=1, min=15, time="any", proof="The snack outdoors"),
    dict(id="cafe-out", t="Have a drink outdoors at {place}", cat="food", needs=["cafe"], effort=2, min=30, time="day", proof="The drink, outside"),
    dict(id="picnic", t="Have a picnic at {place}", cat="food", needs=["park"], effort=4, min=60, time="day", proof="The picnic spread"),
    dict(id="fruit-tree", t="Find a fruit growing on a tree", cat="food", needs=["trees"], effort=3, min=25, time="day", kind="tree", proof="The fruit on the tree"),

    # ---------- rain checks (bad weather: window, balcony, doorway) ----------
    dict(id="rain-sound", t="Open a window and listen to the rain for 3 minutes", cat="rain", needs=[], effort=1, min=5, time="any", wet=True, rain=True, proof="The rainy view from your window"),
    dict(id="rain-drops", t="Photograph raindrops on a window, leaf or railing", cat="rain", needs=[], effort=1, min=5, time="any", wet=True, rain=True, proof="The raindrops"),
    dict(id="storm-sky", t="Photograph the storm clouds from a safe spot", cat="rain", needs=[], effort=1, min=5, time="day", wet=True, rain=True, kind="sky", proof="Dramatic clouds"),
    dict(id="window-bird", t="Watch for a bird from your window for 5 minutes", cat="rain", needs=[], effort=1, min=5, time="day", wet=True, rain=True, kind="bird", proof="Your window view"),
    dict(id="balcony-plant", t="Find a plant enjoying the rain", cat="rain", needs=[], effort=1, min=5, time="day", wet=True, rain=True, kind="plant", proof="The wet plant"),
    dict(id="doorway-air", t="Step to your doorway and take 10 deep breaths of fresh air", cat="rain", needs=[], effort=1, min=3, time="any", wet=True, rain=True, proof="The outside, from your doorway"),
]

# ---------- more variety: night, streets, anywhere (added after the first playtest: nights only had 7 templates) ----------
T += [
    # night
    dict(id="night-walk", t="Take a {n}-minute walk under the street lights", cat="move", needs=[], effort=2, min=15, time="night", proof="Your street at night", params={"n": [10, 15, 20]}),
    dict(id="moon-find", t="Find the moon tonight and photograph it", cat="sky", needs=[], effort=2, min=10, time="night", kind="sky", proof="The moon, any size"),
    dict(id="moth-lamp", t="Find a moth or insect circling a light", cat="nature", needs=[], effort=3, min=15, time="night", kind="insect", proof="The bug near the lamp"),
    dict(id="night-sounds", t="Stand outside for 3 minutes and name {n} night sounds", cat="mindful", needs=[], effort=1, min=5, time="night", proof="Where you stood", params={"n": [3, 5]}),
    dict(id="lit-window", t="Find the most interesting lit-up window or sign on your street", cat="explore", needs=[], effort=2, min=15, time="night", proof="The glowing window or sign"),
    dict(id="night-silhouette", t="Photograph a tree silhouette against the night sky", cat="photo", needs=["trees"], effort=2, min=15, time="night", kind="tree", proof="Dark branches against the sky"),
    dict(id="constellation", t="Find a pattern in the stars and give it your own name", cat="sky", needs=[], effort=2, min=15, time="night", kind="sky", proof="The night sky"),
    dict(id="night-air", t="Step out for 5 minutes of night air, phone in pocket", cat="mindful", needs=[], effort=1, min=5, time="night", proof="Your doorstep at night"),
    dict(id="light-trails", t="Watch traffic lights change {n} times from a street corner", cat="explore", needs=[], effort=1, min=10, time="night", proof="The street corner", params={"n": [3, 5]}),
    dict(id="night-cat", t="Spot a cat or dog out at night", cat="social", needs=[], effort=2, min=15, time="night", kind="animal", proof="The animal (from a respectful distance)"),
    dict(id="shadow-lamp", t="Make a shadow puppet under a street lamp", cat="photo", needs=[], effort=1, min=10, time="night", proof="Your shadow puppet on the ground"),
    dict(id="frogs", t="Listen for frogs or crickets near {place}", cat="water", needs=["water"], effort=3, min=20, time="night", proof="The water at night"),
    # streets, any time
    dict(id="doorstep-sky", t="Look up from your doorstep for 2 full minutes", cat="sky", needs=[], effort=1, min=3, time="any", kind="sky", proof="The sky above your door"),
    dict(id="street-tree", t="Find the biggest tree on your street", cat="nature", needs=[], effort=1, min=10, time="day", kind="tree", proof="The tree"),
    dict(id="street-flower", t="Find a flower growing in a pot, balcony or wall", cat="nature", needs=[], effort=1, min=10, time="day", kind="plant", proof="The flower"),
    dict(id="block-loop", t="Walk once around your block", cat="move", needs=[], effort=1, min=10, time="any", proof="Any corner of your block"),
    dict(id="steps-count", t="Walk {n} steps away from home and photograph what's there", cat="explore", needs=[], effort=2, min=15, time="any", proof="Whatever you found", params={"n": [500, 1000, 2000]}),
    dict(id="chai-walk", t="Walk to get a tea, coffee or juice, and drink it outside", cat="food", needs=[], effort=2, min=20, time="any", proof="The drink outdoors"),
    dict(id="street-food", t="Try a snack from a street stall or local shop, eaten outside", cat="food", needs=[], effort=2, min=20, time="any", proof="The snack outside"),
    dict(id="sign-hunt", t="Find the funniest or strangest sign near you", cat="explore", needs=[], effort=2, min=20, time="day", proof="The sign"),
    dict(id="vehicle-color", t="Count {color} vehicles until you reach {n}", cat="explore", needs=[], effort=1, min=10, time="any", proof="The street you watched", params={"color": ["red", "yellow", "white"], "n": [5, 10]}),
    dict(id="rooftop", t="Go up to your roof, terrace or balcony and look at the horizon", cat="sky", needs=[], effort=1, min=10, time="any", kind="sky", proof="The horizon"),
    dict(id="neighbour-plant", t="Find the most impressive plant someone is growing in your area", cat="nature", needs=[], effort=2, min=15, time="day", kind="plant", proof="The plant (from the street)"),
    dict(id="stray-friend", t="Spot a bird, squirrel or stray animal in your lane", cat="birds", needs=[], effort=2, min=15, time="day", kind="animal", proof="The animal"),
    dict(id="local-temple", t="Walk to the nearest temple, mosque, church or community place and sit outside it", cat="explore", needs=[], effort=2, min=25, time="any", proof="The outside of the place"),
    dict(id="market-walk", t="Walk through your nearest market without buying anything", cat="explore", needs=[], effort=2, min=25, time="day", proof="The market street"),
    dict(id="sunrise", t="Be outside for sunrise", cat="sky", needs=[], effort=4, min=20, time="morning", kind="sky", proof="The early sky"),
    dict(id="dew", t="Find dew drops on a leaf or grass", cat="nature", needs=[], effort=2, min=10, time="morning", kind="plant", proof="The dew"),
    dict(id="dog-walk-along", t="Offer to walk a friend's or neighbour's dog", cat="social", needs=[], effort=3, min=30, time="day", kind="animal", proof="The dog on the walk"),
    dict(id="photo-walk", t="Take {n} photos of things you've never noticed on your street", cat="photo", needs=[], effort=2, min=20, time="day", proof="Your favourite of them", params={"n": [3, 5]}),
]

from scripts.quest_templates_more import templates as _more  # noqa: E402

T += _more()
