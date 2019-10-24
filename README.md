# **ieddit.com**

###### This site is the result of several thousand lines of code written over the past month, there are a LOT of bugs, has only now reached a state I'd describe as 'beta'. While the general layout/design is mostly complete, the UI is still a bit rough in some areas.

### About

The idea behind this project was to offer a website with functionality similar to reddit's, with a focus on transparency, privacy, freedom of expression, and so on, while also trimming down the massive amount of design bloat reddit has accumulated over the years. To attempt to preserve these operating principles, this site will not pursue any form of monetization which would violate the privacy of users, regardless of growth. Additionally, this allows the site to operate fully independently without being beholden to the demands of advertisers.

The wikimedia foundation has proven that such a model is feasible even at the upper echelons of scale, if one is willing to operate leanly without the express pursuit of profit.

Last time this site was re-posted to HN, it was on day 1 of the public alpha. A significant amount has been changed since then - and I'm not asleep this time :) - so hopefully it will go a bit smoother.

### Features

* Fully Transparent Mod/Admin Action Logs

Transparency is essential in trusting those who weld the power to control discussion. While censorship is often necessary, a lack of accountability and/or transparency is never acceptable. An example modlog can be found here [https://ieddit.com/i/ieddit/actions/](https://ieddit.com/i/ieddit/actions/)

* Anonymous Posting Option

The worth of an idea should not solely be judged solely on how popular somebody is, or how well they conform to dogma. Users have the option of posting anonymously with every post/comment, or toggling anonymous by default.

* (optional) Client-side PGP messaging between users.

Thanks to openpgp.js, users have the option of using the built-in pgp messaging system to send messages which, in theory, ensures that any communications will be inaccessible to even those with access to the database. Both public and private keys are stored on the server, but the private key is stored in an incomplete form which should only be useful with the correct passphrase.

This is nowhere close to fully secure, any sort of XSS vuln or other route in which an attacker can modify the code running on the page could result in pass-phrases being gathered. For convenience sake, once a passphrase is set or a message is decrypted, the passphrase is saved into localstorage. While I'll add the option to toggle this functionality this soon, JS in the browser is an inherently insecure environment for this sort of thing.

Users who want to make absolutely sure their communications are truly private should continue to roll their own, locally hosted and thoroughly audited, PGP.

* Fully Transparent Site Operation

Any major site updates/changes will proposed and discussed with the community before implementation. Feedback is essential when gauging the worth of an update, any changes in site operation that are truly, and justifiably, despised will not be forced upon the community. As monetization is not, and will never be, the primary focus of this site, a fair amount of insulation is provided against these sorts of updates.

Site finances will be always remain completely transparent. The site's code is completely open source, and I will do my best to ensure it remains easy to deploy independently. If at any point I am judged to be no longer upholding the principles outlined in this document, users will be able to transition easily to a mirror site operated by somebody they believe will better meet their standards.

* Privacy

Tracking code will never be utilized, user data will never be up for sale. The site attempts to avoid using javascript where possible, and most core functionality can be achieved without. TOR/VPN users currently will have no issues using the site, and I'll make every effort to preserve these options.

As of 10/21/2019, I can confirm the core site functionality still works perfectly in a js-disabled tor browser, and it's honestly been a little painful attempting to preserve it. A few things added recently like user/comment/post blocking will only work with javascript, but support for non-javascript browsers can be added easily if there is demand.

Traffic logs are only stored for 1 day max on the prod server. No other logging information is stored on my end but functionality-related database records.

All static files, JS/CSS/Thumbnails, are hosted locally. The only requests that are sent to external servers happen only during image/video expansion.

### Future

There is a ton of room for UI improvements in the more out-of-the-way areas of the site. Examples being mod options, user settings, etc.

It would be trivial to offer a hidden service option if there is demand for one. As of now, no hidden service option exists, to avoid making the deployment process slightly more tedious and the hosting costs.

I've sunk a solid month of my time into this, and most of the core functionality is now completed, so I'll most likely take a step back and adopt a more gradual pace of development. Areas such as tests, code refactoring, error handling, logging, etc have been neglected due to an emphasis on implementing as many features as possible in a very narrow time window.

### How To Use

If you're familiar with reddit, you already know how to use this site.  Whenever you create a sub, you essentially are creating a mini-community, and become the head moderator responsible for the community. You can then run this community however you wish, and add/remove additional moderators as you need them.

When creating a post, users have the option between creating a post with text, or a url. Every post must go to a sub.

The index page contains all posts from all subs that are not marked nsfw. /i/all contains all posts, including those that are not safe for work.

Users can vote up/down posts and comments. The higher vote total a post/comment has, the higher it appears on the page.

### Rules

Please mark all content you would not want your boss looking over your shoulder and seeing as NSFW. Moderators have the ability to mark entire subs as nsfw.

No Spam.

Nothing that violates US law, or anything that would be considered 'gray area'. US speech protections are some of the strongest and most liberal in the world, if your content pushes the boundaries of these laws, you should probably reconsider posting it.

* To clarify, this rule is aimed mainly at anything which could be considered 'borderline cp'. Loli/Shota, jailbait, &etc. This is not the place for that type of content.

### Finally

[You can find the site code here: https://github.com/cc-d/ieddit](https://github.com/cc-d/ieddit)

### Who am I?

I'm just a random person who is fairly frustrated at the state the internet as of late, especially when it comes to the issues resulting from companies trampling on speech in the pursuit of monetization.

The underlying infrastructure of the internet is fine. Centralization is only an issue if the centralized actor acts with impunity, against the best interests of its users. As seen with youtube, reddit, &c. With transparency and accountability, and without a significant profit incentive to do otherwise, the model still works.

Currently everything is running on google cloud, due to $90 of credit I had on the platform (and they block outgoing port 25... annoying af but hey, it's free). Once this credit runs out, all hosting costs will be coming directly out of my pocket.

As of now, the total costs of running the single prod server, and outgoing proxy servers, are relatively low. When this site was on the front page of HN for nearly an entire day on day 1, it handled just fine once configured correctly on a 1 core 1.6GB vps.

If this site ever starts receiving more traffic than can be handled on using the lowest-tier VPS offerings, I will not be able to sustain it for very long. That being said, unless for some reason the site starts receiving several million requests a day, hosting costs should not go above $20/$30 a month at most.

### Additional Info

Code contributions are HIGHLY welcome.

Bitcoin: 1698YXgDhYdoNqqcjxsGjrPrLb81XWNML5

Monero: 48e8yy7jyjT7RGDheWmr8Phemmxu4Z4haA8eLurKaLxi2CpzAZ5xP5hdHYmB1aJTzji1ToihZLudiHECKVL18gvm3HkqSiz

I can be contacted at the email in my github profile, or on HN/Reddit/this site under the same username.

If you have read this far, I genuinely appreciate your time.

A page with all relevant site usage stats can be found here: [https://ieddit.com/stats/](https://ieddit.com/stats/)

Thank you to all those who have contributed.

### How To Install

#### Linux
The following instructions worked on a fresh debian 9 vps.

run ```sudo bash install.sh```

edit ```config.py``` to the proper values (you should only need to change config.URL)

run ```python3 create_db.py```

start with ```python3 run.py``` or if you want to use a different port ```python3 run.py <PORT>```

the site should be running on localhost:80  or the port you defined - the default username/password for an admin account is 'a' 'a'


#### Windows

If you do not have Python 3 on your machine, install it:
https://www.python.org/downloads/

If you do not have `scoop` package manager, install it:
https://scoop.sh

If you do not have `ruby`, install it:
https://rubyinstaller.org

If you do not have `sqlite3`, install it:
https://www.sqlite.org/download.html (Grab precompiled binaries for SQLite3 and place in C:/Windows/System32 or another directory in your $PATH)

Run `scoop install postgresql`

Run `gem install sqlite3`

Create a Virtualenv and run `pip install -r requirements.txt`

Edit ```config.py``` to the proper values (you should only need to change config.URL)

Run `python3 create_db.py`

This is all you need to setup your development environment on Windows.

To run the server simply run `python3 run.py` and it will spin up the local development server on `localhost:80`.

#### Error monitoring

##### Sentry
You can setup Sentry monitoring on your instance by setting ```SENTRY_ENABLED``` to ```True``` and filling in
```SENTRY_DSN``` in ```config.py```.


<br>
<br>
