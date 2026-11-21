# AR-TECHNO-CRAFT website (rebuilt from the saved home page)

## IMPORTANT: add the images
Your saved file came with a folder named `AR-TECHNO- CRAFT_files`. Copy ALL images (.webp, .jpg, .png, .mp4) from it into `assets/images/`.
File names already match (41.webp, client1.webp, hp1.webp, LOGO4.jpg, bg-mg.webp, video1.mp4 ...). Until then a grey "Add image here" box shows.
Put the certificate PDF at `assets/certificates/1.pdf`.

## Run
- VS Code: install "Live Server", right-click index.html > Open with Live Server (or just double-click index.html).
- Or from the project folder:
  - `npm install`
  - `npm start` then open `http://localhost:8080`

## Build
- `npm run build`

## Pages
Home is complete with the original text. The other pages (About, Values, Certificates, Functions, Products, Infrastructure) have the right menu and layout but need their text copied from the live site (yellow notes). Gallery, Clients and Contact are ready.
Edit text in the HTML files. If you change menus/footer, edit `build.py` and run `python build.py`.
