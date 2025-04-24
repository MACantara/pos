// Initialize variables
let cart = [];
let total = 0;
let discountApplied = false; // Prevent multiple discounts in one transaction

// Function to add items to the cart
function addToCart(item, price) {
    cart.push({ item, price });
    total += price;
    updateCart();
}

// Function to update the cart display
function updateCart() {
    const cartList = document.getElementById("cart-list");
    cartList.innerHTML = "";
    cart.forEach((cartItem) => {
        const li = document.createElement("li");
        li.textContent = `${cartItem.item} - ₱${cartItem.price}`;
        cartList.appendChild(li);
    });

    document.getElementById("total-price").textContent = `Total: ₱${total}`;
}

// Function to handle checkout
function checkout() {
    discountApplied = false; // Reset discount for a new transaction
    const receiptList = document.getElementById("receipt-list");
    const receiptTotal = document.getElementById("receipt-total");
    const discountedTotal = document.getElementById("discounted-total");
    const changeDisplay = document.getElementById("change-display");
    const paymentInput = document.getElementById("payment-input");
    const discountCheckbox = document.getElementById("discount-checkbox");

    // Reset receipt modal
    receiptList.innerHTML = "";
    cart.forEach((cartItem) => {
        const li = document.createElement("li");
        li.textContent = `${cartItem.item} - ₱${cartItem.price}`;
        receiptList.appendChild(li);
    });

    receiptTotal.textContent = `Total: ₱${total}`;
    discountedTotal.textContent = `Discounted Total: ₱${total}`; // Initially no discount
    changeDisplay.textContent = "Change: ₱0";
    paymentInput.value = "";
    discountCheckbox.checked = false;

    document.getElementById("receipt-modal").style.display = "flex";
}

// Function to apply discount to the total only once
function applyDiscount() {
    const discountedTotal = document.getElementById("discounted-total");

    if (!discountApplied) {
        const discount = total * 0.2; // Calculate 20% discount
        const newTotal = total - discount; // Apply discount to total
        discountedTotal.textContent = `Discounted Total: ₱${newTotal.toFixed(2)}`;
        discountApplied = true; // Mark the discount as applied
    } else {
        alert("Discount already applied to this transaction!");
    }
}

// Function to calculate change
function calculateChange() {
    const paymentInput = document.getElementById("payment-input");
    const changeDisplay = document.getElementById("change-display");
    const discountedTotalText = document.getElementById("discounted-total").textContent;
    const discountedTotal = parseFloat(discountedTotalText.replace(/[^\d.]/g, "")); // Extract numeric value

    const payment = parseFloat(paymentInput.value);
    if (!isNaN(payment)) {
        const change = payment - discountedTotal;
        changeDisplay.textContent = `Change: ₱${change >= 0 ? change.toFixed(2) : 0}`;
    }
}

// Function to close the receipt modal
function closeReceipt() {
    document.getElementById("receipt-modal").style.display = "none";
    cart = [];
    total = 0;
    updateCart();

    let cart = [];

function addToCart(itemName, price) {
    const item = {
        name: itemName,
        price: price
    };
    cart.push(item);
    alert(`${itemName} added to your cart.`);
}

function proceedToOrder() {
    localStorage.setItem('cart', JSON.stringify(cart)); // Store cart in localStorage
    window.location.href = 'cart.html'; // Redirect to the cart page
}

}
