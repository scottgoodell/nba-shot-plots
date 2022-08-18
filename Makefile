docker-postgres:
	docker run -d --name my_postgres -p 5432:5432 -e POSTGRES_USERNAME=postgres -e POSTGRES_PASSWORD=postgres postgres

refresh_db:
	rm -rf prisma/migrations
	yes | prisma migrate dev --name init