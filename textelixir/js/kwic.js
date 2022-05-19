// copy to clipboard
const copy = (text) => {
    navigator.clipboard.writeText(text);
}

const copyRow = () => {
    let copyBtn = event.target;
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
    setTimeout (() => {
        tr.innerHTML = originalHTML;
    }, 2000)
}

// copy All
let contents = []
let copyAllBtn = document.querySelector('#copyButton');
copyAllBtn.addEventListener('click', function copyAll() {
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
    setTimeout (() => {
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
showAll.addEventListener('click', function () {
    // wait before getting buttons
    setTimeout(() => {
        
        // Show Functions
        document.querySelectorAll('.btn-showtype').forEach(show_button => {
            show_button.addEventListener('click', function () {
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
            document.querySelectorAll('.btn-alpha').forEach(alpha_button => {
                alpha_button.addEventListener('click', function () {
                    let [direction, dotOrder] = dot.dataset.order;
                    dotOrder = parseInt(dotOrder);
                    let sort_type = alpha_button['id'];
                    const rows = document.querySelectorAll('tbody tr');
                    let done_words = [];
                    let row_array = [];

                    if (sort_type == 'A-Z') {
                        for (let i = 0; i < rows.length; i++) {
                            const currCell = rows[i].querySelectorAll('td')[selectCells[direction]];
                            let inserted = false;

                            if (direction === 'c') {
                                let words = currCell.querySelectorAll('span.w')

                                if (done_words.length > 0) {
                                    for (let itr = 0; itr < done_words.length; itr++) {
                                        if (!inserted) {
                                            for (let cmp = 1; cmp < words.length - 1; cmp++) {
                                                if (words[cmp].innerHTML.localeCompare(done_words[itr][cmp].innerHTML) < 1) {
                                                    if (words[cmp].innerHTML.localeCompare(done_words[itr][cmp].innerHTML) == 0) {
                                                        if (words.length > done_words[itr].length) {
                                                            while (words.length > done_words[itr].length && itr < done_words.length - 1) {
                                                                itr++;
                                                            }
                                                            done_words.splice(itr + 1, 0, words);
                                                            row_array.splice(itr + 1, 0, rows[i]);
                                                            inserted = true;
                                                            break;
                                                        }
                                                        else {
                                                            done_words.splice(itr, 0, words);
                                                            row_array.splice(itr, 0, rows[i]);
                                                            inserted = true;
                                                            break;
                                                        }
                                                    }
                                                    else {
                                                        done_words.splice(itr, 0, words);
                                                        row_array.splice(itr, 0, rows[i]);
                                                        inserted = true;
                                                        break;
                                                    }
                                                }
                                                else {
                                                    break;
                                                }
                                            }
                                        }
                                    }

                                    if (!inserted) {
                                        done_words.push(words);
                                        row_array.push(rows[i]);
                                    }

                                }
                                else {
                                    done_words.push(words);
                                    row_array.push(rows[i])
                                }
                            }

                            else {
                                const currWord = currCell.querySelectorAll('span.w')[dotOrder].innerHTML;
                                if (done_words.length > 0) {
                                    for (let itr = 0; itr < done_words.length; itr++) {
                                        if (currWord.localeCompare(done_words[itr]) < 1) {
                                            done_words.splice(itr, 0, currWord);
                                            row_array.splice(itr, 0, rows[i]);
                                            inserted = true;
                                            break;
                                        }
                                    }
                                    if (!inserted) {
                                        done_words.push(currWord);
                                        row_array.push(rows[i]);
                                    }
                                }
                                else {
                                    done_words.push(currWord);
                                    row_array.push(rows[i])
                                }
                            }
                        }
                    }

                    else {
                        for (let i = 0; i < rows.length; i++) {
                            const currCell = rows[i].querySelectorAll('td')[selectCells[direction]];
                            let inserted = false;

                            if (direction === 'c') {
                                let words = currCell.querySelectorAll('span.w')

                                if (done_words.length > 0) {
                                    for (let itr = 0; itr < done_words.length; itr++) {
                                        if (!inserted) {
                                            for (let cmp = 1; cmp < words.length - 1; cmp++) {
                                                if (words[cmp].innerHTML.localeCompare(done_words[itr][cmp].innerHTML) > -1) {
                                                    if (words[cmp].innerHTML.localeCompare(done_words[itr][cmp].innerHTML) == 0) {
                                                        if (words.length < done_words[itr].length) {
                                                            while (words.length < done_words[itr].length && itr < done_words.length - 1) {
                                                                itr++;
                                                            }
                                                            done_words.splice(itr + 1, 0, words);
                                                            row_array.splice(itr + 1, 0, rows[i]);
                                                            inserted = true;
                                                            break;
                                                        }
                                                        else {
                                                            done_words.splice(itr, 0, words);
                                                            row_array.splice(itr, 0, rows[i]);
                                                            inserted = true;
                                                            break;
                                                        }
                                                    }
                                                    else {
                                                        done_words.splice(itr, 0, words);
                                                        row_array.splice(itr, 0, rows[i]);
                                                        inserted = true;
                                                        break;
                                                    }
                                                }
                                                else {
                                                    break;
                                                }
                                            }
                                        }
                                    }

                                    if (!inserted) {
                                        done_words.push(words);
                                        row_array.push(rows[i]);
                                    }

                                }
                                else {
                                    done_words.push(words);
                                    row_array.push(rows[i])
                                }
                            }

                            else {
                                const currWord = currCell.querySelectorAll('span.w')[dotOrder].innerHTML;
                                let inserted = false;

                                if (done_words.length > 0) {
                                    for (let itr = 0; itr < done_words.length; itr++) {
                                        if (currWord.localeCompare(done_words[itr]) > -1) {
                                            done_words.splice(itr, 0, currWord);
                                            row_array.splice(itr, 0, rows[i]);
                                            inserted = true;
                                            break;
                                        }
                                    }
                                    if (!inserted) {
                                        done_words.push(currWord);
                                        row_array.push(rows[i]);
                                    }
                                }
                                else {
                                    done_words.push(currWord);
                                    row_array.push(rows[i]);
                                }
                            }
                        }
                    }

                    let tbody = document.querySelector('tbody');
                    tbody.innerHTML = '';

                    for (let arr_len = 0; arr_len < row_array.length; arr_len++) {
                        tbody.appendChild(row_array[arr_len]);
                    }

                })
            })

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


// a_z.addEventListener('click', function () {
//     console.log('sort A-Z');
// })
// z_a.addEventListener('click', function () {
//     console.log('sort Z-A')
// })

