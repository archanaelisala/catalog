from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Cloth, Base, Model, User
engine = create_engine('sqlite:///clothsdata.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loades into the
# database session object. Any change made against the objests in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()

session = DBSession()

# Dummy User
User1 = User(
    name="Saral Kumar",
    email="saralkumar238@gmail.com",
    picture="https://pbs.twimg.com/profile_images/ "
            "2671170543/18debd694829ed78203a5a36dd364160_400x400.png"
    )
session.add(User1)
session.commit()

# Menu(list of player) for Country India

cloth1 = Cloth(name="Kids", user_id=1)
session.add(cloth1)
session.commit()

# Model List info
model1 = Model(name="Frock",
                 price="500",
                 color="red",
                 pic="https://cdn.shopify.com/s/files/1/1083/6796/products/product-image-854828235_1024x1024.jpg?v=1543642880",
                 brand="shein",
                 model_id=1,
                 user_id=1
                 )
session.add(model1)
session.commit()

model2 = Model(name="Shirt",
                 price="1000",
                 color="blue",
                 pic="https://i5.walmartimages.com/asr/9fac9355-4150-466a-aed0-6193125059bd_1.a8a78cf81c754b2aae0e07c9292e50b4.jpeg",
                 brand="lauren",
                 model_id=1,
                 user_id=1
                 )
session.add(model2)
session.commit()

cloth2 = Cloth(name="Women", user_id=1)
session.add(cloth2)
session.commit()

# Model List info
model1 = Model(name="Saree",
                 price="5000",
                 color="pink",
                 pic="https://n4.sdlcdn.com/imgs/h/s/w/Jesti-Designer-Pink-Georgette-Saree-SDL164883003-1-cd8d7.jpg",
                 brand="Dharamavaram",
                 model_id=2,
                 user_id=1
                 )
session.add(model1)
session.commit()
model2 = Model(name="Chudidhars",
                 price="1500",
                 color="white",
                 pic="https://www.jagstore.in/product/pretty-chanderi-silk-handwork-suit-4",
                 brand="Dharamavaram",
                 model_id=2,
                 user_id=1
                 )
session.add(model2)
session.commit()

print("List of Models are added!!!")
