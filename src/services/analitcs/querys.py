
class SQLQueryBuilder:

    @staticmethod
    def users_in_research(research_id):
        query = """
        SELECT tg_user_id	
        FROM public.users
        WHERE user_id in (SELECT user_id 
                            FROM public.user_research 
                            WHERE research_id = {research_id})
        """

        return query.format(research_id=research_id)

    @staticmethod
    def assistant_messages(telegram_user_id):
        query = """
        SELECT 
            am.to_user_id,
            am.text,
            am.created_at
        FROM assistant_messages am
        WHERE to_user_id = {telegram_user_id}
        """
        return query.format(telegram_user_id=telegram_user_id)

    @staticmethod
    def user_messages(telegram_user_id):
        query = """
        SELECT 
            um.from_user,
            um.text,
            um.created_at
        FROM user_messages um
        WHERE from_user = {telegram_user_id}
        """
        return query.format(telegram_user_id=telegram_user_id)


