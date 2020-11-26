#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.orm import load_only
from flask import request



#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
# app.config.from_object('config')
# db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db,compare_type=True)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    website=db.Column(db.String(), default='No Website', nullable=True)
    phone = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False, nullable=True)
    seeking_description = db.Column(db.String(), default='Not currently seeking performance venues', nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120),  nullable = True, default=' No Facebook Link')
    website=db.Column(db.String(), nullable = True, default='No Website')
    seeking_venue = db.Column(db.Boolean,  nullable = True, default=False)
    seeking_description = db.Column(db.String(), nullable = True,  default='Not currently seeking performance venues')    


class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime())

    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))

    artist = db.relationship( Artist, backref=db.backref('shows', cascade='all, delete'))
    venue = db.relationship( Venue, backref=db.backref('shows', cascade='all, delete'))


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)
  

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[] 
  locations = Venue.query.distinct('city','state').all()

  for location in locations:
    venues_in_city = Venue.query.filter(Venue.city == location.city, Venue.state == location.state).all()
    venues_records=[]
    for venue_c in venues_in_city:
      venue_shows = Show.query.filter(Show.venue_id==venue_c.id)
      upcoming_shows=0
      for v_show in venue_shows:
        # print(v_show)
        if v_show.start_time>=datetime.now():
          upcoming_shows+=1
      venue_record={
      "id": venue_c.id,
      "name": venue_c.name,
      "num_upcoming_shows": upcoming_shows
      }
      venues_records.append(venue_record)
    record={
        'city':location.city,
        'state':location.state,
        'venues':venues_records
    }
    data.append(record)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=request.form.get('search_term', '')
  # print(search_term)
  data=Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
  count=len(data)
  v_data=[]
  for v in data:
    venue_shows = Show.query.filter(Show.venue_id==v.id)
    upcoming_shows=0
    for v_show in venue_shows:
      if v_show.start_time>=datetime.now():
        upcoming_shows+=1
    venue_record={
      "id": v.id,
      "name": v.name,
      "num_upcoming_shows": upcoming_shows
      }
    v_data.append(venue_record)

  response={
    "count": count,
    "data": v_data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue=Venue.query.filter(Venue.id==venue_id).order_by('id').first()
  # print(venue)
  past_shows_v=[]
  upcoming_shows_v=[]
  venue_shows = Show.query.filter(Show.venue_id==venue.id)
  upcoming_shows_count=0
  past_shows_count = 0
  for v_show in venue_shows:
    artist = Artist.query.filter(Artist.id==v_show.artist_id).order_by('id').first()
    str_time=(v_show.start_time.strftime("%d/%m/%Y, %H:%M"))
    print(str_time)
    record={
      "artist_id":artist.id,
      "artist_name":artist.name,
      "artist_image_link":artist.image_link ,
      "start_time":str_time
    }
    if v_show.start_time>=datetime.now():
      upcoming_shows_count+=1
      upcoming_shows_v.append(record)
    elif v_show.start_time<datetime.now():
      past_shows_count+=1
      past_shows_v.append(record)
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description":venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows_v,
    "upcoming_shows": upcoming_shows_v,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count,
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  v_name=request.form['name']
  v_city=request.form['city']
  v_state=request.form['state']
  v_address=request.form['address']
  v_facebook=request.form['facebook_link']
  tmp_genres = request.form.getlist('genres')
  v_genres = ','.join(tmp_genres)  
  try:
    v=Venue(name=v_name,city=v_city,state=v_state,address=v_address, genres=v_genres, facebook_link=v_facebook)
    print(v.genres)
    db.session.add(v)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' +v_name + ' could not be listed.')
  finally:
    db.session.close()

  # on successful db insert, flash success
  # flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue=Venue.query.get(venue_id)
    # print(venue)
    db.session.delete(venue)
    db.session.commit()
  except:
    print('Failed')
    db.session.rollback()
  finally:
    db.session.close()
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.options(load_only("id", "name")).all()
  # data=[{
  #   "id": 4,
  #   "name": "Guns N Petals",
  # }, {
  #   "id": 5,
  #   "name": "Matt Quevedo",
  # }, {
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  # }]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
 
  search_term=request.form.get('search_term', '')
  # print(search_term)
  data=Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
  count=len(data)
  v_data=[]
  for v in data:
    venue_shows = Show.query.filter(Show.artist_id==v.id)
    upcoming_shows=0
    for v_show in venue_shows:
      if v_show.start_time>=datetime.now():
        upcoming_shows+=1
    venue_record={
      "id": v.id,
      "name": v.name,
      "num_upcoming_shows": upcoming_shows
      }
    v_data.append(venue_record)

  response={
    "count": count,
    "data": v_data
  }
 
 
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 4,
  #     "name": "Guns N Petals",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
 
 

  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist=Artist.query.filter(Artist.id==artist_id).order_by('id').first()
  # print(venue)
  past_shows_v=[]
  upcoming_shows_v=[]
  artist_shows = Show.query.filter(Show.artist_id==artist.id)
  upcoming_shows_count=0
  past_shows_count = 0
  for v_show in artist_shows:
    venue = Venue.query.filter(Venue.id==v_show.venue_id).order_by('id').first()
    str_time=(v_show.start_time.strftime("%d/%m/%Y, %H:%M"))
    print(str_time)
    record={
      "venue_id":venue.id,
      "venue_name":venue.name,
      "venue_image_link":venue.image_link ,
      "start_time":str_time
    }
    if v_show.start_time>=datetime.now():
      upcoming_shows_count+=1
      upcoming_shows_v.append(record)
    elif v_show.start_time<datetime.now():
      past_shows_count+=1
      past_shows_v.append(record)
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description":artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows_v,
    "upcoming_shows": upcoming_shows_v,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count,
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm(request.form)
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  form = ArtistForm(obj=artist)
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    try:
        artist = Artist.query.first_or_404(artist_id)
        form.populate_obj(artist)
        db.session.commit()
        flash(f'Artist {form.name.data} was successfully edited!')
    except ValueError as e:
        db.session.rollback()
        flash(f'An error occurred in {form.name.data}. Error: {str(e)}')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)



@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    try:
        venue = Venue.query.first_or_404(venue_id)
        print(venue)
        form.populate_obj(venue)
        db.session.commit()
        flash(f'Venue {form.name.data} was successfully edited!')
    except ValueError as e:
        db.session.rollback()
        flash(f'An error occurred in {form.name.data}. Error: {str(e)}')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  v_name=request.form['name']
  v_city=request.form['city']
  v_state=request.form['state']
  v_phone=request.form['phone']
  v_facebook=request.form['facebook_link']
  v_genres=request.form['genres']
  # tmp_genres = request.form.getlist('genres')
  # v_genres = ','.join(tmp_genres)  
  try:
    v=Artist(name=v_name,city=v_city,state=v_state,phone=v_phone, genres=v_genres, facebook_link=v_facebook)
    print(v.genres)
    db.session.add(v)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' +v_name + ' could not be listed.')
  finally:
    db.session.close()
  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  initial_data=Show.query.all()

  data=[]
  for d in initial_data:
    v= Venue.query.filter(Venue.id==d.venue_id).first()
    a=Artist.query.filter(Artist.id==d.artist_id).first()
    str_time=(d.start_time.strftime("%d/%m/%Y, %H:%M"))
    record={
    "venue_id": d.venue_id,
    "venue_name": v.name,
    "artist_id": d.artist_id,
    "artist_name": a.name,
    "artist_image_link": a.image_link,
    "start_time": str_time
    }
    data.append(record)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  s_artist_id=request.form['artist_id']
  s_venue_id=request.form['venue_id']
  s_start_date=request.form['start_time']
  try:
    v=Show(artist_id=s_artist_id,venue_id=s_venue_id,start_time=s_start_date)
    db.session.add(v)
    db.session.commit()
    flash('Show ' + request.form['artist_id'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show  could not be listed.')
  finally:
    db.session.close()
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
