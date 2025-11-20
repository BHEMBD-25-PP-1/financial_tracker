from sqlalchemy import create_engine, text

# Настройки подключения
DB_USER = "postgres"
DB_PASSWORD = "4410"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "test_db"

# Создаём движок SQLAlchemy
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

with engine.connect() as conn:
    query = text("""
        SELECT pid, usename, application_name, client_addr, state, backend_start
        FROM pg_stat_activity
        ORDER BY backend_start DESC;
    """)
    result = conn.execute(query)

    print(f"{'PID':<8}{'User':<15}{'App':<30}{'Client IP':<15}{'State':<10}{'Start Time'}")
    print("-" * 100)
    for row in result:
        pid, usename, app_name, client_addr, state, backend_start = row

        # Заменяем все None на пустую строку
        pid = pid or ""
        usename = usename or ""
        app_name = app_name or ""
        client_addr = client_addr or ""
        state = state or ""
        backend_start = backend_start or ""

        print(f"{pid:<8}{usename:<15}{str(app_name):<30}{str(client_addr):<15}{str(state):<10}{str(backend_start)}")