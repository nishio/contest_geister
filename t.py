import client

ai = client.PartiallyObservableAI()
ai.choose_red_ghosts()
ai = client.Sub()
print ai.choose_next_move(client.TEST_GHOSTS)
