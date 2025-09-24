let cart = [];

function addToCart(id, name, price) {
  cart.push({id, name, price});
  alert(name + ' added to cart!');
}

function prepareCheckout(e) {
  document.getElementById('cart_data').value = JSON.stringify(cart);
  document.getElementById('total').value = cart.reduce((sum, item) => sum + item.price, 0);
}
