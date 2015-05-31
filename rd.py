import rdio
import pickle


def main(manager=None):
    if (manager==None):
        manager = get_authorized_rdio_manager()
    tracks = get_tracks_from_txt('example_playlist.txt', manager)
    manager.add_to_collection(tracks)

    

def get_tracks_from_txt(txt_name, manager):
    f = open(txt_name,'r')
    tracks = []
    for line in f:
        if len(line.rsplit())==0: continue
        # get artist/album info
        artist, album = artist_album_from_line(line)

        # get the tracks to add.
        tracks = (tracks + get_tracks_from_artist_and_album(artist, album, manager))
    #self.tracks = tracks
    #self.viz_tracks_to_add()
    return tracks

def artist_album_from_line(line):
    tmp = line.split(',')
    if len(tmp)==1:
        artist = tmp[0].rstrip()
        album = ''
    elif len(tmp)==2:
        artist = tmp[0].rstrip().strip()
        album = tmp[1].rstrip().strip()
    return artist, album

def get_tracks_from_artist_and_album(artist_search_string, 
                                     album_search_string, manager):
    search = manager.search(
        artist_search_string, 
        ['Artist'])
    if len(search.results)==0: return []
    # take only first artist.
    artist = search.results[0]
    print ' '
    print 'ARTIST: searched "%s", got "%s"' % (
        artist_search_string.encode('utf-8'), 
        artist.name.encode('utf-8'))

    '''
    artist_browser = artist.browse().load()
    # this is a hack to make sure all of the albums have 
    # loaded before we proceed.
    artist_browser.albums
    len0 = len(artist_browser.albums)-1
    from time import sleep
    while len(artist_browser.albums)>len0:
        sleep(1)
        len0 = len(artist_browser.albums)

    if len(artist_browser.albums)==0: return []
    if type(album_search_string)!=str: return []
    '''

    # process this album.
    print 'album string is %s'%(album_search_string)
    if album_search_string=='':
        results = get_tophit_tracks_from_artist(artist, manager)
    elif album_search_string.lower()=='all':
        results = get_all_albums_from_artist(artist, manager)
    else:
        results = get_one_album(album_search_string, 
                               artist, manager)
    if not(isinstance(results,list)):
        results = [results]
    return results




def get_all_albums_from_artist(artist, manager, count=20):
    albums = manager.get_albums_for_artist(artist.key, count=count)
    if albums==None: albums=[]
    output = [item for album in albums for item in album.track_keys]
    return output

def get_tophit_tracks_from_artist(artist, manager, count=10):
    tracks = manager.get_tracks_for_artist(artist.key, count=count)
    if tracks==None: tracks=[]
    output = [track.key for track in tracks]
    return output

def get_one_album(album_search_string,
                  artist, manager):
    album = None
    album_words = album_search_string.split()
    albums = manager.get_albums_for_artist(artist.key, count=100)
    if albums==None: return []
    for this_album in albums:
        this_album_name = this_album.name.lower().encode('utf-8')
        score = 0.
        possible_score = 0.
        for word in album_words:
            if word.lower() in this_album_name: score += len(word)
            possible_score += len(word)
        frac_score = score/possible_score
        print this_album_name, frac_score
        if ((score>2) & (frac_score>0.5)):
            album = this_album
            #print '  album: %s --- %s'%(
            #    album_search_string.encode('utf-8'), 
            #    this_album.name.encode('utf-8'))
            break

        # if we couldn't find that album, try to grab the 
        # "top hit" tracks from this artist.
    if album==None:
        return get_tophit_tracks_from_artist(artist, manager)
    return album.track_keys


def get_authorized_rdio_manager(user_email='rkeisler@gmail.com', api_key=None, api_secret=None):
    # USER_EMAIL is the email address of the user whose account you want access to.
    # you can get your own API_KEY and API_SECRET from 
    # http://rdio.mashery.com/member/register

    # Setup the API manager. If you have an ACCESS_KEY and ACCESS_SECRET for a
    # particular user, you can pass that in as the third and forth arguments
    # to Api().
    if ((api_key==None) | (api_secret==None)):
        api_key, api_secret = get_api_info()

    rdio_manager = rdio.Api(api_key, api_secret)
    user = rdio_manager.find_user(user_email)
    print '%s %s key is: %s.' % (user.first_name, user.last_name, user.key)

    # Set authorization: get authorization URL, then pass back the PIN.
    token_dict = rdio_manager.get_token_and_login_url()
    print 'Authorize this application at: %s?oauth_token=%s' % (
        token_dict['login_url'], token_dict['oauth_token'])

    token_secret = token_dict['oauth_token_secret']
    oauth_verifier = raw_input('Enter the PIN / oAuth verifier: ').strip()
    #token = raw_input('Enter oauth_token parameter from URL: ').strip()
    token = token_dict['oauth_token']
    request_token = {"oauth_token":token, "oauth_token_secret":token_secret}

    authorization_dict = rdio_manager.authorize_with_verifier(oauth_verifier, request_token)

    # Get back key and secret. rdio_manager is now authorized
    # on the user's behalf.
    print 'Access token key: %s' % authorization_dict['oauth_token']
    print 'Access token secret: %s' % authorization_dict['oauth_token_secret']

    return rdio_manager


def get_api_info():
    f = open('my_rdio_api','r') 
    line = f.next()
    return line.split(',')
