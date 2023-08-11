async function selectChange() {
    await main_update()
    await rose_update()
    await time_update()
    await length_update()
};

async function main_update() {
    await main()
}

async function main2_update() {
    await main2()
}

async function rose_update() {
    await rose()
}

const endTime = {
    '11': "2022-06-29T23:45:00",
    '12': "2022-06-29T23:45:00",
    '13': "2022-04-29T23:45:00",
    '14': "2022-04-29T23:45:00",
    '15': "2022-06-29T23:45:00",
    '16': "2021-10-30T23:45:00",
    '17': "2022-04-29T23:45:00",
    '18': "2022-05-30T23:45:00",
    '19': "2022-12-30T23:45:00",
    '20': "2021-10-30T23:45:00"
}

async function turb_update() {
    let timeDom = document.getElementById('time-input');
    let turbDom = document.getElementById('turb-input')
    let turbId = turbDom.value;
    console.log('pre-endTime[turbId]',timeDom.value)
    timeDom.value = endTime[turbId]
    console.log('post-endTime[turbId]',timeDom.value)
}

async function time_update() {

}

async function length_update() {

}
