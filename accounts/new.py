from django.db import connection



def search(request):
    query = request.GET['q']
    sql = f"SELECT * FROM some_table WHERE title LIKE '%{query}%';"

    cursor = connection.cursor()
    print(cursor.execute(sql))