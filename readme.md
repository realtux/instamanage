## instamanage

unfollow those who haven't followed you back. **no instagram api required**

this is a tool to unfollow those who haven't followed you back. it does it by pulling all the followers off the account and pulling all the following off the account and comparing the two. this data is saved in a `state.json` file so that the followers/following download does not have to be done each time.

### install
```
pip install requests
pip install 'requests[security]'
git clone https://github.com/ebrian/instamanage
cd instamanage
cp config_sample.json config.json
python instamanage.py
```

### maximum action rates observed without temp/perm ban
- likes: 1000 daily, 500 hourly
- unfollow: 200 daily, 65 hourly
