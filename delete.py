import asyncio
import aiohttp

async def main():
    url = "https://api.github.com/repositories"
    headers = {"Accept": "application/vnd.github.v3+json"}
    like_db = []
    counter = 0
    async with aiohttp.ClientSession() as session:
        while url or counter != 2:
            async with session.get(str(url), headers=headers, ssl=False) as response:
                counter += 1
                result =  await response.json()
                print(result[0]["full_name"])
                return result[0]["id"]
                # like_db.append(repositories)
                # url = response.headers.get('Link', '').split(';')[0].strip('<>').split(',')[0].split('?')[0].split('>')[0] if 'next' in response.headers.get('Link', '') else None

if __name__ == "__main__":
    asyncio.run(main())