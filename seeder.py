from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from genre_setup import Genre, Base, Movie, User

engine = create_engine('sqlite:///movies.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()
User1 = User(name="Mohammed Almuqbil", email="mywork3mal@gmail.com",
             picture='https://www.hdbfs.com/sites/default/files/images/img/hdb-icons/Personal-loan.png')
session.add(User1)
session.commit()


genre1 = Genre(user_id=1, name="Action")

session.add(genre1)
session.commit()

movie1_1 = Movie(name="The Equalizer", bio="A man believes he has put his mysterious past behind him and has dedicated himself to beginning a new, quiet life. But when he meets a young girl under the control of ultra-violent Russian gangsters, he can't stand idly by - he has to help her.",
                      genre=genre1)

session.add(movie1_1)
session.commit()


movie2_1 = Movie(name="Mad Max: Fury Road", bio="In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler in search for her homeland with the aid of a group of female prisoners, a psychotic worshiper, and a drifter named Max.",
                      genre=genre1)

session.add(movie2_1)
session.commit()


movie3_1 = Movie(name="Logan", bio="In the near future, a weary Logan cares for an ailing Professor X. However, Logan's attempts to hide from the world and his legacy are upended when a young mutant arrives, pursued by dark forces.",
                      genre=genre1)

session.add(movie3_1)
session.commit()


genre2 = Genre(user_id=1, name="Drama")

session.add(genre2)
session.commit()


movie1_2 = Movie(name="Logan", bio="In the near future, a weary Logan cares for an ailing Professor X. However, Logan's attempts to hide from the world and his legacy are upended when a young mutant arrives, pursued by dark forces.",
                      genre=genre2)

session.add(movie1_2)
session.commit()


genre3 = Genre(user_id=1, name="Comedy")

session.add(genre3)
session.commit()


genre4 = Genre(user_id=1, name="Animation")

session.add(genre4)
session.commit()


genre5 = Genre(user_id=1, name="Adventure")

session.add(genre5)
session.commit()


genre6 = Genre(user_id=1, name="Fantasy")

session.add(genre6)
session.commit()


genre7 = Genre(user_id=1, name="Romantic")

session.add(genre7)
session.commit()


genre8 = Genre(user_id=1, name="Horror")

session.add(genre8)
session.commit()


genre9 = Genre(user_id=1, name="Biography")

session.add(genre9)
session.commit()


genre10 = Genre(user_id=1, name="Mystery")

session.add(genre10)
session.commit()

print "movie added !"
