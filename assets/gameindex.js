let currentPage = 1;
let itemsPerPage = 20; // Default items per page
const selectedTags = new Set();
const filterTagsContainer = document.getElementById('filterTagsContainer');
const itemsPerPageContainer = document.getElementById('itemsPerPage');
const cardsContainer = document.querySelector('.cardContainer');
const cards = Array.from(document.querySelectorAll('.card')); // Convert NodeList to Array for easy manipulation
let maxCards = cards.length;
const currentPageSpan = document.getElementById('currentPage');

// Event Listeners
document.getElementById('itemsPerPage').addEventListener('change', function() {
    itemsPerPage = this.value;
    currentPage = 1; // Reset to the first page
    updateDisplay(false); //dont sort
});
document.getElementById('firstPage').addEventListener('click', function() {
    if (currentPage > 1) {
        currentPage = 1;
        updateDisplay(false); //dont sort
    }
});
document.getElementById('prevPage').addEventListener('click', function() {
    if (currentPage > 1) {
        currentPage--;
        updateDisplay(false); //dont sort
    }
});
document.getElementById('nextPage').addEventListener('click', function() {
    const totalPages = Math.ceil(maxCards / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        updateDisplay(false); //dont sort
    }
});
document.getElementById('lastPage').addEventListener('click', function() {
    const totalPages = Math.ceil(maxCards / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage = totalPages || 1;
        updateDisplay(false); //dont sort
    }
});

document.getElementById('filterInput').addEventListener('input', updateDisplay);
document.getElementById('statusFilter').addEventListener('change', updateDisplay);
document.getElementById('sortOrder').addEventListener('change', updateDisplay);
document.getElementById('resetButton').addEventListener('click', resetFilters);
document.querySelectorAll('.tag').forEach(tag => {
    tag.addEventListener('click', function() {
        const tagText = this.textContent;
        if (selectedTags.has(tagText)) {
            selectedTags.delete(tagText);
            this.classList.remove('selected');
        } else {
            selectedTags.add(tagText);
            this.classList.add('selected');
        }
        updateFilterTagsContainer(); // Update the filter tags container
        updateDisplay(); // Then update the card display
    });
});

function updateFilterTagsContainer() {
    filterTagsContainer.innerHTML = '';
    selectedTags.forEach(tag => {
        const tagEl = document.createElement('span');
        tagEl.textContent = tag;
        tagEl.classList.add('tag', 'selected'); // 'selected' class for styling
        tagEl.addEventListener('click', function() {
            selectedTags.delete(tag);
            this.classList.remove('selected');
            updateFilterTagsContainer(); // Update the filter tags container
            updateDisplay(); // Then update the card display
        });
        filterTagsContainer.appendChild(tagEl);
    });
    updateDisplay();
}

// Update display based on filters, sort order, and pagination
function updateDisplay(doSort=true) {
    if(!!doSort){
        cards.sort( (a,b) => applySort(a,b) );
    }
    cardsContainer.innerHTML = '';
    cards.forEach(card => cardsContainer.appendChild(card));

    //Hide all cards
    cards.forEach(card => {
        card.style.display = 'none'; 
    });

    let filteredGames = cards.filter(card => applyAllFilters(card));
    
    maxCards = filteredGames.length;
    if(currentPage > Math.ceil(maxCards / itemsPerPage)){
        currentPage = 1; // or Math.ceil(maxCards / itemsPerPage) ? Not sure...
    }
    currentPageSpan.innerHTML = currentPage;

    paginateAndDisplay(filteredGames);
}

// Apply all filters
function applyAllFilters(card) {
    return applyTagFilter(card) && 
            applyTextFilter(card) && 
            applyStatusFilter(card) &&
            applyDomainFilter(card);
}

// Pagination and Display
function paginateAndDisplay(games) {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    games.forEach((card, index) => {
        card.style.display = (index >= startIndex && index < endIndex) ? '' : 'none';
    });
}

function applyTagFilter(card) {
    if (selectedTags.size === 0) return true; // No tag filter applied
    const cardTags = Array.from(card.querySelectorAll('.tag')).map(tag => tag.textContent);
    return [...selectedTags].every(tag => cardTags.includes(tag));
}

function applyTextFilter(card) {
    const filterText = document.getElementById('filterInput').value.toLowerCase();
    if (filterText.length < 3) return true; // No text filter applied
    const title = card.querySelector('.card-title').textContent.toLowerCase();
    return title.includes(filterText);
}

function applyStatusFilter(card) {
    const filterValue = document.getElementById('statusFilter').value;
    switch (filterValue) {
        case 'active':
            return (!card.classList.contains('abandoned') && !card.classList.contains('completed'));
        case 'completed':
            return card.classList.contains('completed');
        case 'abandoned':
            return card.classList.contains('abandoned');
        case 'any':
        default:
            return true;
    }
}

function applySort(a, b) {
    const sortOrder = document.getElementById('sortOrder').value;
    switch (sortOrder) {
        case 'alphabetical':
            return a.querySelector('.card-title').textContent.localeCompare(b.querySelector('.card-title').textContent);
        case 'lastUpdated':
            return new Date(b.dataset.updated || "1970-01-01") - new Date(a.dataset.updated || "1970-01-01"); //descending order
        case 'newest':
            return new Date(b.dataset.published || "1970-01-01") - new Date(a.dataset.published || "1970-01-01"); //descending order
        case 'oldest':
            return new Date(a.dataset.published || "1970-01-01") - new Date(b.dataset.published || "1970-01-01"); //descending order
        case 'random':
            return Math.random() - 0.5;
        default:
            return 0;
    }
}

function resetFilters() {
    // Reset text filter
    const filterInput = document.getElementById('filterInput');
    filterInput.value = '';
    
    // Reset status filter
    const statusFilter = document.getElementById('statusFilter');
    statusFilter.value = 'any';

    // Reset sort order
    const sortOrder = document.getElementById('sortOrder');
    sortOrder.value = 'alphabetical';

    const domainFilter = document.getElementById('domainFilter');
    domainFilter.value = 'all'

    // Reset tags filter
    selectedTags.clear();
    document.querySelectorAll('.tag.selected').forEach(tag => {
        tag.classList.remove('selected');
    });
    updateFilterTagsContainer();

    // Reset pagination to the first page
    currentPage = 1;
    itemsPerPage = 20;
    const itemsPerPageContainer = document.getElementById('itemsPerPage');
    itemsPerPageContainer.value = String(itemsPerPage)
    
    // Update the display
    updateDisplay();
}

//Initial display
updateDisplay()


/**
 *  Lightbox code below
 */
let currentImageIndex = 0;
let images = [];


let wheelEventTimer = null;

function debounce(func, delay) {
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(wheelEventTimer);
        wheelEventTimer = setTimeout(() => func.apply(context, args), delay);
    };
}

function handleWheelEvent(event) {
    if (event.deltaY < 0) {
        // Scrolling up
        previousImage();
    } else {
        // Scrolling down
        nextImage();
    }
}

const delay = 150;
const debouncedWheelEvent = debounce(handleWheelEvent, delay); 


function openLightbox(name,imgList) {
    images = imgList;
    currentImageIndex = 0;
    const lightboxTitle = document.getElementById('lightboxTitle');
    lightboxTitle.innerHTML = decodeURI(name);
    
    document.getElementById('lightbox').style.display = 'block';
    updateLightboxImage();
    disableScroll();
}

function closeLightbox() {
    const imgElement = document.getElementById('lightboxImg');
    imgElement.src = "";
    const captionElement = document.getElementById('caption');
    captionElement.innerHTML = "";
    const lightboxTitle = document.getElementById('lightboxTitle');
    lightboxTitle.innerHTML = "";
    document.getElementById('lightbox').style.display = 'none';
    enableScroll();
}

function disableScroll() {
    // Add a class to the body that prevents scrolling
    document.body.classList.add('no-scroll');
}

function enableScroll() {
    // Remove the class from the body that prevents scrolling
    document.body.classList.remove('no-scroll');
}

function updateLightboxImage() {
    const imgElement = document.getElementById('lightboxImg');
    imgElement.src = images[currentImageIndex];

    // Left click for next image
    imgElement.onclick = function() {
        nextImage();
    };

    // Right click for previous image
    imgElement.oncontextmenu = function(event) {
        event.preventDefault(); // Prevent the browser context menu
        previousImage();
        return false; // Prevent default context menu
    };

    // Mouse wheel for navigation
    imgElement.onwheel = debouncedWheelEvent;

    // Update caption or other elements if needed
    const captionElement = document.getElementById('caption');
    captionElement.innerHTML = (currentImageIndex+1) + " / " + images.length + " ( " + images[currentImageIndex] +" )"
}

function nextImage() {
    if (currentImageIndex < images.length - 1) {
        currentImageIndex++;
    } else {
        currentImageIndex = 0; // Loop back to the first image
    }
    updateLightboxImage();
}

function previousImage() {
    if (currentImageIndex > 0) {
        currentImageIndex--;
    } else {
        currentImageIndex = images.length - 1; // Loop to the last image
    }
    updateLightboxImage();
}
    
function randomImage() {
    currentImageIndex = Math.floor(Math.random() * images.length);
    updateLightboxImage();
}

// Keyboard navigation
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeLightbox();
    } else if (event.key === 'ArrowRight') {
        nextImage();
    } else if (event.key === ' ') {
        nextImage();
    } else if (event.key === 'ArrowLeft') {
        previousImage();
    } else if (event.key === 'r') {
        randomImage();
    }
});

// Close lightbox when clicking outside the image
document.getElementById('lightbox').addEventListener('click', function(event) {
    if (event.target === this) {
        closeLightbox();
    }
});

/**
 * Create Domain / Source filter
 */
function populateDomainFilter() {
    const domainSet = new Set();
    cards.forEach(card => {
        const urlElement = card.querySelector('.card-title'); // Assuming the URL is in an <a> inside .card-title
        const url = new URL(urlElement.href);
        const domain = url.hostname;
        domainSet.add(domain);
    });

    const domainFilter = document.getElementById('domainFilter');
    domainSet.forEach(domain => {
        const option = document.createElement('option');
        option.value = domain;
        option.textContent = domain;
        domainFilter.appendChild(option);
    });
}
document.getElementById('domainFilter').addEventListener('change', updateDisplay);

function applyDomainFilter(card) {
    const selectedDomain = document.getElementById('domainFilter').value;
    if (selectedDomain === 'all') return true;

    const urlElement = card.querySelector('.card-title');
    const url = new URL(urlElement.href);
    const domain = url.hostname;
    return domain === selectedDomain;
}

// Call this function to populate the TLD filter
document.addEventListener('DOMContentLoaded', populateDomainFilter);