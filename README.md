# **ieddit.com**

###### This is an __alpha__ version of this website. It's the result of a few thousand lines of code written in only two weeks, there are a LOT of bugs, and the design is nowhere near final. I focused on getting __something__ out as fast as possible, in order to gauge interest. Even the name isn't set in stone.
### About

The idea behind this project was to offer a website with functionality similar to reddit's, with a focus on transparency, privacy, freedom of expression, and so on, while also trimming down the massive amount of design bloat reddit has accumulated over the years. To attempt to preserve these operating principles, this site will not pursue any form of monetization which would violate the privacy of users, regardless of growth. Additionally, this allows the site to operate fully independently without being beholden to the demands of advertisers.

The wikimedia foundation has proven that such a model is feasible even at the upper echelons of scale, if one is willing to operate leanly without the express pursuit of profit.

### How To Install
The following instructions worked on a fresh debian 9 vps.

run ```sudo bash install.sh```

edit ```config.py``` to the proper values (you should only need to change config.URL)

run ```python3 create_db.py```

start with ```python3 run.py```

the site should be running on localhost:80 - the default username/password for an admin account is 'a' 'a'

### Features

* Fully Transparent Mod/Admin Action Logs
	
Transparency is essential in trusting those who weld the power to control discussion. While censorship is often necessary, a lack of accountability and/or transparency is never acceptable.

* Anonymous Posting Option

The worth of an idea should not solely be judged solely on how popular somebody is, or how well they conform to dogma.

* Fully Transparent Site Operation

Any major site updates/changes will proposed and discussed with the community before implementation. Feedback is essential when gauging the worth of an update, any changes in site operation that are truly, and justifiably, despised will not be forced upon the community. As monetization is not, and will never be, the primary focus of this site, a fair amount of insulation is provided against these sorts of updates.

Site finances will be always remain completely transparent. The site's code is completely open source, and I will do my best to ensure it remains easy to deploy independently. If at any point I am judged to be no longer upholding the principles outlined in this document, users will be able to transition easily to a mirror site operated by somebody they believe will better meet their standards.

* Privacy

Tracking code will never be utilized, user data will never be up for sale. The site attempts to avoid using javascript where possible, and most core functionality can be achieved without. TOR/VPN users currently will have no issues using the site, and I'll make every effort to preserve these options.


### Future

At this stage of development, there is still an immense amount of work to be done. The ability to subscribe to subs will be added relatively soon, currently with zero traffic an opt-in model would not work well, as I'd have to set defaults. Some general things I'd like to see in the future are: a hidden service option, easy to use client-side javascript pgp messaging between users, much better caching than is currently implemented (basically none!), and so on.


### How To Use

If you're familiar with reddit, you already know how to use this site.  Whenever you create a sub, you essentially are creating a mini-community, and become the head moderator responsible for the community. You can then run this community however you wish, and add/remove additional moderators as you need them.

When creating a post, users have the option between creating a post with text, or a url. Every post must go to a sub.

The index page contains all posts from all subs that are not marked nsfw. /r/all contains all posts, including those that are not safe for work.

Users can vote up/down posts and comments. The higher vote total a post/comment has, the higher it appears on the page.

### Rules

Please mark all content you would not want your boss looking over your shoulder and seeing as NSFW. Moderators have the ability to mark entire subs as nsfw.

No Spam.

Nothing that violates US law, or anything that would be considered 'gray area'. US speech protections are some of the strongest and most liberal in the world, if your content pushes the boundries of these laws, you should probably reconsider posting it.

* To clarify, this rule is aimed mainly at anything which could be considered 'borderline cp'. Loli/Shota, jailbait, &etc. This is not the place for that type of content.

### Finally

[You can find the site code here: https://github.com/cc-d/ieddit](https://github.com/cc-d/ieddit)

### Who am I?

I'm just a random person who can write bad code and is fairly frustrated at the state the internet as of late, especially when it comes to the issues of censorship and privacy. Decentralized platforms are not an ideal solution for internet communities. TOR is also not an answer, the technical barrier in accessing hidden services alone disqualifies them as a practical alternative, before even considering the bandwidth/latency limitations.

The underlying infrastructure of the internet is fine. A centralized internet platform is still the most practical solution... centralization is only an issue if the centralized actor acts with impunity, against the best interests of its users. As seen with youtube, reddit, &c. With transparency and accountability, and without a significant profit incentive to do otherwise, the model still works.

I may have misjudged the demand for such a platform, if so I'll have lost no more than a few weeks of my life, and will know I at least put effort forward in providing an alternative.

Currently everything is running on google cloud, due to $90 of credit I had on the platform (and they block outgoing port 25... annoying af but hey, it's free). Once this credit runs out, I will not be able to sustain the site under any real amount of use for long financially.

To contribute to server operations, for now the most practical option is crypto. If there ends up being significant demand for a platform like this, I'll go through the motions of setting up additional donation options. Server credit would also be immensely helpful, especially if it's on one of the big guys like aws.

Code contributions are HIGHLY welcome.

Patreon: [https://www.patreon.com/ieddit](https://www.patreon.com/ieddit)

Bitcoin: 1698YXgDhYdoNqqcjxsGjrPrLb81XWNML5

Monero: 48e8yy7jyjT7RGDheWmr8Phemmxu4Z4haA8eLurKaLxi2CpzAZ5xP5hdHYmB1aJTzji1ToihZLudiHECKVL18gvm3HkqSiz

I can be contacted at the email in my github profile, or on HN/Reddit/this site under the same username.

If you have read this far, I genuinely appreciate your time.


<br>
<br>
