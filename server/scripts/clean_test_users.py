from app.db import users, attempts

test_prefixes = ["Test_", "Explorer_"]
query = {"$or": [{"handle": {"$regex": f"^{p}"}} for p in test_prefixes]}

u_matches = list(users.find(query, {"_id": 1, "handle": 1}))
u_ids = [u["_id"] for u in u_matches]
print(f"Found {len(u_matches)} test users: {[u['handle'] for u in u_matches]}")

if u_ids:
    ur = users.delete_many({"_id": {"$in": u_ids}})
    ar = attempts.delete_many({"user_id": {"$in": u_ids}})
    print(f"Successfully deleted {ur.deleted_count} users and {ar.deleted_count} attempts.")
else:
    print("No test users found.")
