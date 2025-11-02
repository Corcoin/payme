addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(req) {
  if(req.method !== "POST") return new Response("Method not allowed", { status: 405 });

  const { recipient, amount, transaction_id } = await req.json();

  const PAYPAL_CLIENT_ID = "YOUR_CLIENT_ID";
  const PAYPAL_SECRET = "YOUR_SECRET";
  const PAYPAL_API = "https://api-m.paypal.com"; // Live

  // 1️⃣ Get access token
  const tokenRes = await fetch(`${PAYPAL_API}/v1/oauth2/token`, {
    method: "POST",
    headers: {
      "Authorization": "Basic " + btoa(`${PAYPAL_CLIENT_ID}:${PAYPAL_SECRET}`),
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: "grant_type=client_credentials"
  });
  const { access_token } = await tokenRes.json();

  // 2️⃣ Calculate 90% payout
  const payout_amount = (parseFloat(amount) * 0.9).toFixed(2);

  // 3️⃣ Send payout
  const payoutRes = await fetch(`${PAYPAL_API}/v1/payments/payouts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${access_token}`
    },
    body: JSON.stringify({
      sender_batch_header: {
        sender_batch_id: crypto.randomUUID(),
        email_subject: "You received a payout!"
      },
      items: [{
        recipient_type: "EMAIL",
        amount: { value: payout_amount, currency: "USD" },
        receiver: recipient,
        note: "Payout after 10% platform fee",
        sender_item_id: crypto.randomUUID()
      }]
    })
  });

  const payoutResult = await payoutRes.json();
  return new Response(JSON.stringify({ success: true, payout: payoutResult }), { status: 200 });
}
