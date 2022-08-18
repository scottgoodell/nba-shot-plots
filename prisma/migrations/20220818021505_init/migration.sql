-- CreateTable
CREATE TABLE "game_finals" (
    "id" SERIAL NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "game_id" TEXT NOT NULL,
    "game_date" TEXT NOT NULL,
    "away_team_id" INTEGER NOT NULL,
    "home_team_id" INTEGER NOT NULL,

    CONSTRAINT "game_finals_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "game_finals_game_id_key" ON "game_finals"("game_id");
