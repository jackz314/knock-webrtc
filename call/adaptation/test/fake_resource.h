/*
 *  Copyright 2019 The WebRTC Project Authors. All rights reserved.
 *
 *  Use of this source code is governed by a BSD-style license
 *  that can be found in the LICENSE file in the root of the source
 *  tree. An additional intellectual property rights grant can be found
 *  in the file PATENTS.  All contributing project authors may
 *  be found in the AUTHORS file in the root of the source tree.
 */

#ifndef CALL_ADAPTATION_TEST_FAKE_RESOURCE_H_
#define CALL_ADAPTATION_TEST_FAKE_RESOURCE_H_

#include <string>

#include "call/adaptation/resource.h"

namespace webrtc {

// Fake resource used for testing.
class FakeResource : public Resource {
 public:
  explicit FakeResource(ResourceUsageState usage_state);
  ~FakeResource() override;

  void set_usage_state(ResourceUsageState usage_state);
};

}  // namespace webrtc

#endif  // CALL_ADAPTATION_TEST_FAKE_RESOURCE_H_
