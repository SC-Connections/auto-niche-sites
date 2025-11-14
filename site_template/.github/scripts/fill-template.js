const axios = require('axios');
const fs = require('fs');

const RAPIDAPI_URL = 'https://amazon-real-time-api.p.rapidapi.com/deals';
const RAPIDAPI_KEY = process.env.RAPID_KEY;
const KEYWORD = process.env.KEYWORD || 'products';

async function fetchAmazonData() {
  try {
    console.log(`🔍 Fetching Amazon data for: ${KEYWORD}`);
    
    const response = await axios.get(RAPIDAPI_URL, {
      headers: {
        'x-rapidapi-host': 'amazon-real-time-api.p.rapidapi.com',
        'x-rapidapi-key': RAPIDAPI_KEY
      },
      params: {
        domain: 'US',
        node_id: '16310101'
      }
    });

    if (response.status === 200 && response.data) {
      const products = response.data.data || [];
      
      // Transform products to our format
      const formattedProducts = products.slice(0, 10).map((product, index) => ({
        id: index + 1,
        title: product.title || 'Product',
        price: product.price || 'N/A',
        rating: product.rating || 'N/A',
        image: product.image || '',
        link: product.link || '#',
        description: product.description || ''
      }));

      const output = {
        keyword: KEYWORD,
        fetched_at: new Date().toISOString(),
        products: formattedProducts
      };

      // Write to filled.json
      fs.writeFileSync('_data/filled.json', JSON.stringify(output, null, 2));
      console.log(`✅ Successfully fetched ${formattedProducts.length} products`);
      
    } else {
      console.error(`⚠️ API returned status ${response.status}`);
      createEmptyData();
    }
  } catch (error) {
    console.error(`❌ Error fetching data: ${error.message}`);
    createEmptyData();
  }
}

function createEmptyData() {
  const output = {
    keyword: KEYWORD,
    fetched_at: new Date().toISOString(),
    products: []
  };
  fs.writeFileSync('_data/filled.json', JSON.stringify(output, null, 2));
}

// Ensure _data directory exists
if (!fs.existsSync('_data')) {
  fs.mkdirSync('_data');
}

fetchAmazonData();
