#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if not username or not password:
            return {'error': 'Username and password are required'}, 422

        try:
            user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            user.password_hash = password

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id

            user_schema = UserSchema()
            return user_schema.dump(user), 201

        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists'}, 422
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')

        if user_id:
            user = db.session.get(User, user_id)
            if user:
                user_schema = UserSchema()
                return user_schema.dump(user), 200

        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            user_schema = UserSchema()
            return user_schema.dump(user), 200

        return {'error': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')

        if user_id:
            session.pop('user_id', None)
            return '', 204

        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')

        if not user_id:
            return {'error': 'Unauthorized'}, 401

        recipes = Recipe.query.all()
        recipe_schema = RecipeSchema(many=True)
        return recipe_schema.dump(recipes), 200

    def post(self):
        user_id = session.get('user_id')

        if not user_id:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json()

        title = data.get('title')
        instructions = data.get('instructions')
        minutes_to_complete = data.get('minutes_to_complete')

        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id
            )

            db.session.add(recipe)
            db.session.commit()

            recipe_schema = RecipeSchema()
            return recipe_schema.dump(recipe), 201

        except ValueError as e:
            db.session.rollback()
            return {'error': str(e)}, 422
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)