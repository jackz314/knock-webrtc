/*
 *  Copyright (c) 2018 The WebRTC project authors. All Rights Reserved.
 *
 *  Use of this source code is governed by a BSD-style license
 *  that can be found in the LICENSE file in the root of the source
 *  tree. An additional intellectual property rights grant can be found
 *  in the file PATENTS.  All contributing project authors may
 *  be found in the AUTHORS file in the root of the source tree.
 */

#ifndef CALL_RTP_VIDEO_SENDER_INTERFACE_H_
#define CALL_RTP_VIDEO_SENDER_INTERFACE_H_

#include <map>
#include <vector>

#include "absl/types/optional.h"
#include "call/rtp_config.h"
#include "modules/rtp_rtcp/include/rtp_rtcp_defines.h"
#include "modules/rtp_rtcp/source/rtp_sequence_number_map.h"
#include "modules/utility/include/process_thread.h"
#include "modules/video_coding/include/video_codec_interface.h"

namespace webrtc {
class VideoBitrateAllocation;
struct FecProtectionParams;

class RtpVideoSenderInterface : public EncodedImageCallback {
 public:
  virtual void RegisterProcessThread(ProcessThread* module_process_thread) = 0;
  virtual void DeRegisterProcessThread() = 0;

  // RtpVideoSender will only route packets if being active, all
  // packets will be dropped otherwise.
  virtual void SetActive(bool active) = 0;
  // Sets the sending status of the rtp modules and appropriately sets the
  // RtpVideoSender to active if any rtp modules are active.
  virtual void SetActiveModules(const std::vector<bool> active_modules) = 0;
  virtual bool IsActive() = 0;

  virtual void OnNetworkAvailability(bool network_available) = 0;
  virtual std::map<uint32_t, RtpState> GetRtpStates() const = 0;
  virtual std::map<uint32_t, RtpPayloadState> GetRtpPayloadStates() const = 0;

  virtual void DeliverRtcp(const uint8_t* packet, size_t length) = 0;

  virtual void OnBitrateAllocationUpdated(
      const VideoBitrateAllocation& bitrate) = 0;
  virtual void OnBitrateUpdated(uint32_t bitrate_bps,
                                uint8_t fraction_loss,
                                int64_t rtt,
                                int framerate) = 0;
  virtual void OnTransportOverheadChanged(
      size_t transport_overhead_bytes_per_packet) = 0;
  virtual uint32_t GetPayloadBitrateBps() const = 0;
  virtual uint32_t GetProtectionBitrateBps() const = 0;
  virtual void SetEncodingData(size_t width,
                               size_t height,
                               size_t num_temporal_layers) = 0;
  virtual absl::optional<RtpSequenceNumberMap::Info> GetSentRtpPacketInfo(
      uint32_t ssrc,
      uint16_t seq_num) const = 0;
};
}  // namespace webrtc
#endif  // CALL_RTP_VIDEO_SENDER_INTERFACE_H_
