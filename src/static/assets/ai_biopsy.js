// Env variables
const maxImagesPermitted = 7;
const baseApiUrl = 'api'
// End Env variables

let token = getCookie('ai-biopsy-auth');
checkTokenAndRedirectIfEmpty();

document.getElementById('year').innerHTML = new Date().getFullYear();
for (var element of document.getElementsByClassName('max-number-of-images')) {
    element.innerHTML = `${maxImagesPermitted}`;
}

setInterval(function(){
    checkTokenAndRedirectIfEmpty();
}, 5000);

function checkTokenAndRedirectIfEmpty() {
    token = getCookie('ai-biopsy-auth');
    if (window.location.pathname !== '/login' && token === '') {
        window.location.href = '/login';
    }
}

function login(event) {
    postLoginData(event.srcElement.username.value, event.srcElement.password.value, baseApiUrl);
}

function postLoginData(username, password, baseApiUrl) {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', `${baseApiUrl}/login`, true);
    let formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    xhr.onload = (e) => {
        if (xhr.status === 200) {
            window.location.href = '/';
        } else {
            document.getElementById('login-form-username-password-error').classList.remove('hidden');
        }
    };
    xhr.onerror = (e) => alert('An error occurred!');
    xhr.send(formData);
}

const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', (event) => { 
        event.preventDefault();
        login(event);
    })
}

function getCookie(cookieName) {
    var name = cookieName + '=';
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return '';
}

function average(array) {
    return array.reduce((a,b) => a + b, 0) / array.length;
}

function isAnImage(file) {
    if (file && (file.type || file.name)) {
        return file.type.startsWith('image/jpeg') || file.type.startsWith('image/png') || file.type.startsWith('image/tiff') || file.name.endsWith('.dcm');
    }

    return false;
};

function getFormData(files) {
    const formData = new FormData();
    for (const file of files) {
        if (isAnImage(file)) {
            formData.append('image', file, file.name);
        }
    }

    return formData;
};

function calculateCumulativeResult() {
    const cancerResults = [];
    const highRiskResults = [];
    const currentImagesKeys = Object.keys(currentImages);

    for (const x of currentImagesKeys) {
        if (currentImages[x].result) {
            if (Number(currentImages[x].result.cancer) > Number(currentImages[x].result.benign)) {
                cancerResults.push(currentImages[x]);
            }
            if (Number(currentImages[x].result.high) > Number(currentImages[x].result.low)) {
                highRiskResults.push(currentImages[x]);
            }
        }
    }

    const result = { model1: 'N/A', model2: 'N/A'};
    if (currentImagesKeys.length) {
        result.model1 = 'Undetermined';
        if (cancerResults.length >= 1) {
            result.model1 = 'Cancer';
        } else if (currentImagesKeys.length >= 7) {
            result.model1 = 'Benign';
        }
    
        if (result.model1 === 'Cancer') {
            result.model2 = 'Undetermined';
            if (highRiskResults.length >= 2) {
                result.model2 = 'High Risk';
            } else if (currentImagesKeys.length >= 7) {
                result.model2 = 'Low Risk';
            }
        }
    }

    return result;
};

resultBadges = {
    'N/A': { badge: '<span class="new badge" data-badge-caption>N/A</span>', description: 'Not applicable', group: 'Generic' },
    'Undetermined': { badge: '<span class="new grey badge" data-badge-caption>Undetermined</span>', description: 'More images are required in order to make a decision.', group: 'Generic' },
    'Cancer': { badge: '<span class="new red darken-4 badge" data-badge-caption>Cancer</span>', description: 'Cancer has been detected.', group: 'Prostate Tissue Assessment' },
    'Benign': { badge: '<span class="new green badge" data-badge-caption>Benign</span>', description: 'No cancer has been detected.', group: 'Prostate Tissue Assessment' },
    'High Risk': { badge: '<span class="new orange darken-4 badge" data-badge-caption>High Risk</span>', description: 'Cancer cells are poorly differentiated (grade group = 3, 4, and 5)', group: 'Risk Assessment' },
    'Low Risk': { badge: '<span class="new orange badge" data-badge-caption>Low Risk</span>', description: 'Cancer cells are likely to grow slowly (grade group = 1 and 2)', group: 'Risk Assessment' },
};

function updateResultsUI(result) {
    if (result) {
        const model1Result = document.getElementById('model1-result');
        const model2Result = document.getElementById('model2-result');
        if (model1Result && model2Result) {
            model1Result.innerHTML = `<a class="waves-effect waves-light modal-trigger" href="#result-explanation-modal">${resultBadges[result.model1].badge}</a>`;
            model2Result.innerHTML = `<a class="waves-effect waves-light modal-trigger" href="#result-explanation-modal">${resultBadges[result.model2].badge}</a>`;
        }
    }
};

function populateExplanations() {
    const badgesExplanationSection = document.getElementById('badges-explanation');
    if (!badgesExplanationSection) {
        return;
    }

    const badgesExplanation = {}
    for (const key of Object.keys(resultBadges)) {
        const group = resultBadges[key].group;
        if (!badgesExplanation[group]) {
            badgesExplanation[group] = [];
        }

        badgesExplanation[group].push(resultBadges[key]);
    }

    for (const key of Object.keys(badgesExplanation)) {
        badgesExplanationSection.innerHTML += 
        `<div class="margin-bottom-default"><h6>${key}</h6>${badgesExplanation[key].map(x => `<div class="margin10">${x.badge} - ${x.description}</div>`).join('')}</div>`;
    }
};

function initializeExplanationsModal() {
    populateExplanations();
    document.addEventListener('DOMContentLoaded', function() {
        const elements = document.querySelectorAll('.modal');
        const instances = M.Modal.init(elements, undefined);
    });
};

function postFormData(formData, baseApiUrl) {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', `${baseApiUrl}/upload`, true);
    xhr.setRequestHeader('Authorization','Basic ' + token);

    var loaders = [...document.getElementsByClassName('loader')];
    xhr.onload = function (e) {
        loaders.map(x => x.classList.add('hidden'));
        if (xhr.status === 200) {
            response = JSON.parse(e.target.response);
            Object.keys(response).map(fileName => {
                currentImages[fileName].result = response[fileName];
                const card = document.getElementById(`image-card-${fileName}`);
                const bar1 = card.getElementsByClassName('bar')[0];
                const goodText1 = card.getElementsByClassName('good-text1')[0];
                const poorText1 = card.getElementsByClassName('poor-text1')[0];
                const goodPercentage1 = (response[fileName].benign * 100).toFixed(2);
                const poorPercentage1 = (response[fileName].cancer * 100).toFixed(2);
                bar1.setAttribute('style', `width:${goodPercentage1}%;`);
                bar1.innerHTML = `&nbsp;`;
                goodText1.innerHTML = `${goodPercentage1}%`;
                poorText1.innerHTML = `${poorPercentage1}%`;

                const bar2 = card.getElementsByClassName('bar')[1];
                const goodText2 = card.getElementsByClassName('good-text2')[0];
                const poorText2 = card.getElementsByClassName('poor-text2')[0];
                const goodPercentage2 = (response[fileName].low * 100).toFixed(2);
                const poorPercentage2 = (response[fileName].high * 100).toFixed(2);
                bar2.setAttribute('style', `width:${goodPercentage2}%;`);
                bar2.innerHTML = `&nbsp;`;
                goodText2.innerHTML = `${goodPercentage2}%`;
                poorText2.innerHTML = `${poorPercentage2}%`;

                const result = card.getElementsByClassName('results')[0];
                result.classList.remove('hidden');
            });
            updateResultsUI(calculateCumulativeResult());
        } else {
            alert('An error occurred!');
        }
    };
    xhr.onerror = () => {
        loaders.map(x => x.classList.add('hidden'));
    };

    xhr.send(formData);
};

function removeImageCard(imageName) {
    const card = document.getElementById(`image-card-${imageName}`);
    imagesPlaceholder.removeChild(card);
    delete currentImages[imageName];
    imageRemovedUpdateUI();
    updateResultsUI(calculateCumulativeResult());
};

function imageRemovedUpdateUI() {
    addImagesButton.classList.remove('disabled');
    if (Object.keys(currentImages).length === 0) {
        clearAllButton.classList.add('disabled');
    }
};

function imageAddedUpdatedUI(numberOfImagesIfAccepted, maxImagesPermitted) {
    if (numberOfImagesIfAccepted > maxImagesPermitted) {
        errorMessage.classList.remove('hidden');
    } else {
        errorMessage.classList.add('hidden');
        clearAllButton.classList.remove('disabled');
        if (numberOfImagesIfAccepted === maxImagesPermitted) {
            addImagesButton.classList.add('disabled');
        }
    }
};

function clearAllImageCards() {
    Object.keys(currentImages).map(image => {
        removeImageCard(image)
    });
};

async function getDcmImage(file) {
    const width = 256;
    const height = 256;
    let pixelData = null;

    function str2ab(str) {
        var buf = new ArrayBuffer(str.length*2); // 2 bytes for each char
        var bufView = new Uint16Array(buf);
        var index = 0;
        for (var i=0, strLen=str.length; i<strLen; i+=2) {
            var lower = str.charCodeAt(i);
            var upper = str.charCodeAt(i+1);
            bufView[index] = lower + (upper <<8);
            index++;
        }
        return bufView;
    };

    const toBase64 = file => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });

    const base64 = await toBase64(file);
    const base64PixelData = base64.substring(base64.indexOf('base64,') + 'base64,'.length);
    const pixelDataAsString = atob(base64PixelData);
    pixelData = str2ab(pixelDataAsString);

    function getPixelData() {
        return pixelData;
    }

    var image = {
        imageId: file.name,
        minPixelValue : 0,
        maxPixelValue : 257,
        slope: 1.0,
        intercept: 0,
        windowCenter : 127,
        windowWidth : 256,
        getPixelData: getPixelData,
        rows: height,
        columns: width,
        height: height,
        width: width,
        color: false,
        columnPixelSpacing: .8984375,
        rowPixelSpacing: .8984375,
        sizeInBytes: width * height * 2
    };

    return new Promise((resolve) => {
        resolve(image);
    });
}

function createImagesUIFromFiles(files, imagesPlaceholder) {
    if (files === null || files === undefined || imagesPlaceholder === null || imagesPlaceholder === undefined) {
        return;
    }

    for (var file of files) {
        const imagePlaceholder = document.createElement('div');
        imagePlaceholder.classList.add('image-card');
        imagePlaceholder.id = `image-card-${file.name}`;
        imagePlaceholder.innerHTML = `
            <div class="card image-container">
                <div class="card-image" ></div>
                <div class="card-file-name">${file.name}</div>
                
                <div class="loader"></div> 
                <div class="delete-image-button" onclick="removeImageCard('${file.name}')">
                    <i class="material-icons">clear</i>
                </div>
                <div class="results card-content hidden">
                    <ul class="collapsible">
                        <li>
                            <div class="collapsible-header">Image Results</div>
                            <div class="collapsible-body">
                                <div class="poor">
                                    <div class="good bar"></div>
                                </div>
                                <div class="legend-item"><div class="legend-marker good"></div>Benign: <span class="good-text1"></span></div>
                                <div class="legend-item"><div class="legend-marker poor"></div>Cancer: <span class="poor-text1"></span></div>
                                </br>
                                <div class="poor">
                                    <div class="good bar"></div>
                                </div>
                                <div class="legend-item"><div class="legend-marker good"></div>Low Risk: <span class="good-text2"></span></div>
                                <div class="legend-item"><div class="legend-marker poor"></div>High Risk: <span class="poor-text2"></span></div>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>`;

        imagesPlaceholder.appendChild(imagePlaceholder);
        var elems = imagePlaceholder.querySelectorAll('.collapsible');
        var instances = M.Collapsible.init(elems, undefined);
        const cardImage = imagePlaceholder.getElementsByClassName('card-image')[0];

        if (file.name.endsWith('.dcm')) {
            cornerstone.enable(cardImage);
            getDcmImage(file).then(function(image) {
                cornerstone.displayImage(cardImage, image);
            });
        } else {
            cardImage.innerHTML = `<img alt="${file.name}" width="330px" />`;
        }

        const image = cardImage.children[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            image.setAttribute('src', e.target.result);
        };

        reader.readAsDataURL(file);
    }
};

function submit(images, baseApiUrl) {
    postFormData(getFormData(images), baseApiUrl);
};

function handleFiles(files, baseApiUrl) {
    if (files && files.length) {
        const images = [...files].filter(file => isAnImage(file));
        let numberOfcurrentImages = Object.keys(currentImages).length;
        const imagesToSend = [];
        (images).map(image => {
            if (typeof(currentImages[image.name]) === 'undefined') {
                imagesToSend.push(image);
            }
        });

        const numberOfImagesIfAccepted = imagesToSend.length + numberOfcurrentImages;
        imageAddedUpdatedUI(numberOfImagesIfAccepted, maxImagesPermitted);
        if (numberOfImagesIfAccepted <= maxImagesPermitted) {
            imagesToSend.map(image => { currentImages[image.name] = image; });
            createImagesUIFromFiles(imagesToSend, imagesPlaceholder);
            submit(imagesToSend, baseApiUrl);
        }
    }
};

function dropHandler(event) {
    handleFiles(event.dataTransfer.files, baseApiUrl);
};

function preventDefaults (e) {
    e.preventDefault();
    e.stopPropagation();
}

const form = document.getElementById('file-form');
const errorMessage = document.getElementById('error-message');
const currentImages = {};
const addImagesButton = document.getElementById('add-images-button');
const results = document.getElementById('results-placeholder');
const fileSelect = document.getElementById('file-select');

updateResultsUI(calculateCumulativeResult());
if (fileSelect) {
    fileSelect.value = '';
    fileSelect.addEventListener('change', function(e) {
        handleFiles(e.target.files, baseApiUrl);
    });
}

const clearAllButton = document.getElementById('clear-all-button');
if (clearAllButton) {
    clearAllButton.addEventListener('click', () => { clearAllImageCards(); } );
}

const imagesPlaceholder = document.getElementById('imageCards-placeholder');
if (imagesPlaceholder) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        imagesPlaceholder.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        imagesPlaceholder.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        imagesPlaceholder.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        imagesPlaceholder.classList.add('highlight');
    };
    
    function unhighlight(e) {
        imagesPlaceholder.classList.remove('highlight');
    };
}

initializeExplanationsModal();