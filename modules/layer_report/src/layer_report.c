/*
 * レイヤーが変わるたびに、raw HID で Mac に知らせる。
 * 送る中身（32 バイト）: 'R' 'L' 一番上のレイヤー番号  有効なレイヤーのビット（下位 8 ビット）
 * Mac から 'R' 'L' で始まる報告を受け取ったら、今の状態をもう一度送る（小窓の起動時用）。
 */
#include <zephyr/kernel.h>
#include <string.h>

#include <zmk/event_manager.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/keymap.h>
#include <raw_hid/events.h>

static uint8_t report[CONFIG_RAW_HID_REPORT_SIZE];

static void send_state(struct k_work *work) {
    memset(report, 0, sizeof(report));
    report[0] = 'R';
    report[1] = 'L';
    report[2] = zmk_keymap_highest_layer_active();
    report[3] = (uint8_t)(zmk_keymap_layer_state() & 0xFF);
    raise_raw_hid_sent_event((struct raw_hid_sent_event){.data = report, .length = sizeof(report)});
}

static K_WORK_DEFINE(send_work, send_state);

static int on_layer_changed(const zmk_event_t *eh) {
    k_work_submit(&send_work);
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(roba_layer_report, on_layer_changed);
ZMK_SUBSCRIPTION(roba_layer_report, zmk_layer_state_changed);

static int on_raw_hid_received(const zmk_event_t *eh) {
    const struct raw_hid_received_event *ev = as_raw_hid_received_event(eh);
    if (ev && ev->length >= 2 && ev->data[0] == 'R' && ev->data[1] == 'L') {
        k_work_submit(&send_work);
    }
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(roba_layer_query, on_raw_hid_received);
ZMK_SUBSCRIPTION(roba_layer_query, raw_hid_received_event);
