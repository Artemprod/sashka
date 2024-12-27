
class SQLQueryBuilder:

    @staticmethod
    def users_in_done_research(research_id):
        query = """
        SELECT tg_user_id	
        FROM public.users
        WHERE user_id in (SELECT user_id 
                            FROM public.archived_user_research 
                            WHERE research_id = {research_id})
        """

        return query.format(research_id=research_id)

    @staticmethod
    def users_in_progress_research(research_id):
        query = """
          SELECT tg_user_id	
          FROM public.users
          WHERE user_id in (SELECT user_id 
                              FROM public.user_research 
                              WHERE research_id = {research_id})
          """

        return query.format(research_id=research_id)

    @staticmethod
    def assistant_messages(telegram_user_id,research_id):
        query = """
        SELECT 
            am.user_telegram_id,
            am.text,
            am.created_at
        FROM assistant_messages am
        WHERE user_telegram_id = {telegram_user_id} and research_id = {research_id}
        """
        return query.format(telegram_user_id=telegram_user_id,research_id=research_id)

    @staticmethod
    def user_messages(telegram_user_id,research_id):
        query = """
        SELECT
            um.user_telegram_id,
            um.text,
            um.created_at
        FROM user_messages um
        WHERE user_telegram_id = {telegram_user_id} and research_id = {research_id}
        """
        return query.format(telegram_user_id=telegram_user_id,research_id=research_id)


