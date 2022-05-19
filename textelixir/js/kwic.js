// copy to clipboard
const copy = (text) => {
    navigator.clipboard.writeText(text);
}

const copyRow = () => {
    let copyBtn = event.srcElement;
    let tr = copyBtn.parentElement.parentElement;
    let originalHTML = tr.innerHTML;
    children = tr.children;
    let before = children[0].innerText;
    let hit = children[1].innerText;
    let after = children[2].innerText;
    copied_text = `${before}\t${hit}\t${after}`;
    copy(copied_text);
    let copied = '<img src="textelixir/img/clipboard-check-solid.svg" class="btn-sm copyBtn align-right">'
    copyBtn.remove();
    tr.children[2].innerHTML += copied;
    setTimeout(() => {
        tr.innerHTML = originalHTML;
    }, 2000)
}

// copy All
let contents = []
let copyAllBtn = document.querySelector('#copyButton');
copyAllBtn.addEventListener('click', () => {
    let i = 0;
    document.querySelectorAll('tbody tr td').forEach(column => {
        text = column.innerText;
        if (i < 2) {
            contents.push(text, '\t');
        }
        if (i == 2) {
            contents.push(text, '\n');
        }
        i++;
        if (i > 2) { i = 0 };
    })
    copy(contents);
    copyAllBtn.value = 'Copied';
    setTimeout(() => {
        copyAllBtn.value = 'Copy All';
    }, 2000)
})


// dot options
const selectCells = {
    'l': 0,
    'c': 1,
    'r': 2
}

const showWordTypes = {
    'lemma': 'lemma',
    'word': 'text',
    'POS': 'pos'
}

// showAll options 
let showAll = document.querySelector('#showAll')
showAll.addEventListener('click', () => {
    // wait before getting buttons
    setTimeout(() => {

        // Show Functions
        document.querySelectorAll('.btn-showtype').forEach(show_button => {
            show_button.addEventListener('click', () => {
                let show = showWordTypes[show_button['value']];
                document.querySelectorAll('tbody tr td span.w').forEach(word => {
                    word.innerHTML = word.dataset[show];
                });

            })
        });

    }, 200);

})

document.querySelectorAll('.dot').forEach(dot => {
    dot.addEventListener('click', function () {
        // wait before getting buttons
        setTimeout(() => {
            document.querySelectorAll('.btn-alpha').forEach(alphaButton => {
                alphaButton.addEventListener('click', function () {
                    let sortType = alphaButton['value']; // 'A-Z' || 'Z-A'
                    let [direction, dotOrder] = dot.dataset.order; // direction: 'l' || 'c' || 'r' , dotOrder: 0.0 || 1.0 || 2.0 ...
                    dotOrder = parseInt(dotOrder);

                    // Create an array of objects that contains the innerHTML of each row and the word that is being sorted on.
                    const rowHTML = document.querySelectorAll('tbody tr');
                    let rows = Array.from(rowHTML)
                        .reduce((acc, curr, idx) => {
                            // Get an array of all the words
                            const words = direction === 'c' ? null : curr.querySelectorAll('td')[selectCells[direction]].querySelectorAll('span.w');
                            if (words) {
                                // 'I'
                                var selectedWord = words[dotOrder].textContent;
                                // 'am.the.best.programmer' || 'programmer.best.the.am'
                                var otherWords = Array.from(words).map((el) => el.textContent);
                                otherWords = direction === 'l' ? otherWords.slice(0, dotOrder).reverse().join('.') : otherWords.slice(dotOrder+1).join('.');
                            }
                            acc.push({
                                innerHTML: curr.innerHTML,
                                // Use the entire <td> cell if the direction is 'c'. Otherwise, just use a specific word from the KWIC lines.
                                sortWord: words === null ? curr.querySelectorAll('td')[selectCells[direction]].textContent : `${selectedWord}.${otherWords}`
                            })
                            return acc;
                        }, [])
                        // Sort by the sort word.
                        .sort((a,b) => {
                            return sortType === 'A-Z' ? a.sortWord.localeCompare(b.sortWord) : b.sortWord.localeCompare(a.sortWord);
                        });
                    // Remove values from <tbody>
                    let tbody = document.querySelector('tbody')
                    tbody.innerHTML = '';
                    // Add sorted rows to <tbody>
                    rows.forEach(({innerHTML}) =>  tbody.innerHTML += innerHTML);
                })
            });

            // Show Functions
            document.querySelectorAll('.btn-showtype').forEach(show_button => {
                show_button.addEventListener('click', function () {
                    let [direction, dotOrder] = dot.dataset.order;
                    dotOrder = parseInt(dotOrder);
                    let show = showWordTypes[show_button['value']];
                    const rows = document.querySelectorAll('tbody tr');
                    for (let i = 0; i < rows.length; i++) {
                        const currCell = rows[i].querySelectorAll('td')[selectCells[direction]];
                        if (direction === 'c') {
                            for (let w of currCell.querySelectorAll('span.w')) {
                                w.innerHTML = w.dataset[show];
                            }
                        } else {
                            const currWord = currCell.querySelectorAll('span.w')[dotOrder];
                            currWord.innerHTML = currWord.dataset[show];
                        }
                    }
                })
            });
        }, 200);
    })
});
